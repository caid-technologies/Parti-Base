"""Stage 3: variant generation per seed.

================================ OVERVIEW ====================
This is the CONDUCTOR for Stage 3. For each clean seed project it produces three
kinds of variant and saves each one to its own JSON file in out/variants/:

  - prompt rewrites      → uses the LLM (asks the model to rephrase the request
                           3 ways: beginner / intermediate / expert)
  - positive variants    → programmatic transforms (no LLM) from
                           programmatic_variants.py
  - evaluation negatives → programmatic defect injection (no LLM), same file

Why split it this way? An early attempt asked the LLM to generate WHOLE variant
records, but the schema is too intricate and the model produced dozens of schema
errors per attempt. The lesson: only use the LLM for the EASY, low-structure
bit (rewriting a sentence) and do the structured edits in plain Python.

Two robustness features worth knowing:
  - Each variant is written to disk THE MOMENT it's made, so if the run is
    interrupted halfway, finished work isn't lost.
  - Re-running SKIPS any variant file that already exists (a cache). Pass
    `force=True` to regenerate from scratch.
============================================================================
"""
from __future__ import annotations
import copy
import json
from pathlib import Path

# The only LLM call in this file goes through chat_json (talks to local Ollama).
from .ollama_client import chat_json
from .programmatic_variants import (
    PROGRAMMATIC_NEGATIVE_DEFECTS,
    PROGRAMMATIC_POSITIVE_AXES,
    make_evaluation_negative,
    make_positive_variants,
)
from .validate import is_valid


# --- LLM: prompt rewrites --------------------------------------------------
# This JSON schema is handed to the model to FORCE its output shape: an object
# with a "prompts" key holding EXACTLY 3 strings. Constraining the model this
# tightly is why the rewrite step is reliable where full-record generation wasn't.

_REWRITE_SCHEMA = {
    "type": "object",
    "required": ["prompts"],
    "properties": {
        "prompts": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {"type": "string", "minLength": 15, "maxLength": 800},
        },
    },
    "additionalProperties": False,
}


def _rewrite_prompts(seed_rec: dict) -> list[str]:
    """Ask the LLM for 3 differently-phrased versions of the project's request.

    Builds a system + user message describing the project and the 3 tones we
    want, sends it to the model with the strict schema above, and returns the
    list of 3 prompt strings. This is the ONLY place the model is invoked.
    """
    name = seed_rec["project"]["name"]
    summary = seed_rec["project"].get("summary", "")
    orig = seed_rec["project"]["original_prompt"]
    system = (
        "You write realistic user requests for hobbyist hardware projects. "
        "Return only the JSON object requested."
    )
    user = (
        f"Project: {name}\n"
        f"Summary: {summary}\n"
        f"Original request: {orig}\n\n"
        f"Write exactly 3 different ways a hobbyist might phrase the same "
        f"request. Use these tones in order:\n"
        f"  1. Beginner — short, casual, may not know precise terminology\n"
        f"  2. Intermediate — clearer requirements, mentions some specs\n"
        f"  3. Expert — detailed constraints, names specific parts, "
        f"dimensions, or budget\n\n"
        f"Each prompt must be standalone (no references to a previous prompt). "
        f"Do not mention component IDs or parts not in the original request. "
        f"Return JSON: {{\"prompts\": [\"...\", \"...\", \"...\"]}}."
    )
    result = chat_json(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        schema=_REWRITE_SCHEMA,
        temperature=0.9,
        max_tokens=2000,
    )
    return result["prompts"]


def _make_rewrites(seed_rec: dict, project_id: str) -> list[dict]:
    """Turn the 3 rewritten prompts into 3 full variant records.

    Each rewrite is just the seed record with a NEW prompt swapped in (the parts,
    relationships, etc. stay identical — only the way the user "asked" changes).
    The `try/except` means a flaky LLM call logs a warning and returns an empty
    list instead of crashing the whole run.
    """
    try:
        prompts = _rewrite_prompts(seed_rec)
    except Exception as e:
        # Catch ANY error from the network/model call so one bad seed can't abort
        # an 18-minute batch. `e` holds the error details for the log line.
        print(f"  [{project_id}] rewrites failed: {e}")
        return []
    variants: list[dict] = []
    # `enumerate(prompts, start=1)` numbers the rewrites 1, 2, 3.
    for i, prompt in enumerate(prompts, start=1):
        v = copy.deepcopy(seed_rec)               # clone the seed
        v["project"]["original_prompt"] = prompt.strip()   # swap in new wording
        v["project"]["variant_type"] = "prompt_rewrite"
        v["project"]["seed_project_id"] = project_id
        v["project"]["project_id"] = f"{project_id}__rewrite_{i}"
        variants.append(v)
    return variants


# --- orchestrator ----------------------------------------------------------

def generate_variants(
    seeds: list[tuple[str, dict]],
    out_dir: Path,
    seed: int = 0,
    force: bool = False,
    positive_axes_per_seed: int | None = None,
    negatives_per_seed: int | None = None,
    enable_rewrites: bool = True,
) -> dict[str, int]:
    """Generate variants for every clean seed.

    Per seed:
      - 3 prompt rewrites (LLM, optional)
      - All 5 positive axes (or `positive_axes_per_seed` if specified)
      - All 4 evaluation negatives (or `negatives_per_seed` if specified)

    Returns aggregate stats.
    """
    # `seed` retained for back-compat callers; deterministic ordering means
    # we don't need it. `_ = seed` just marks it intentionally unused.
    _ = seed
    out_dir.mkdir(parents=True, exist_ok=True)
    # Running tallies returned at the end so the caller can print a summary.
    stats = {
        "seeds_processed": 0,
        "seeds_skipped_invalid": 0,
        "rewrites_written": 0,
        "positives_written": 0,
        "negatives_written": 0,
    }

    # Decide which axes/defects to use. By default ALL of them; the optional
    # caps let smoke tests do fewer. `list[:n]` slices the first n items.
    all_positive_labels = list(PROGRAMMATIC_POSITIVE_AXES.keys())
    all_negative_codes = list(PROGRAMMATIC_NEGATIVE_DEFECTS.keys())
    positive_labels = (
        all_positive_labels[:positive_axes_per_seed]
        if positive_axes_per_seed is not None else all_positive_labels
    )
    negative_codes = (
        all_negative_codes[:negatives_per_seed]
        if negatives_per_seed is not None else all_negative_codes
    )

    # Main loop: process one seed at a time.
    for slug, seed_rec in seeds:
        project_id = seed_rec["project"]["project_id"]

        # Only build variants from seeds that are themselves valid — garbage in
        # would mean garbage variants.
        if not is_valid(seed_rec):
            stats["seeds_skipped_invalid"] += 1
            print(f"[skip] {project_id} - seed fails strict validation")
            continue

        stats["seeds_processed"] += 1
        print(f"[seed] {project_id}")

        # --- LLM rewrites (the only step that calls the model) ---
        if enable_rewrites:
            # Work out the 3 filenames this seed's rewrites would have.
            rewrite_targets = [
                out_dir / f"{project_id}__rewrite_{i}.json" for i in (1, 2, 3)
            ]
            # Only call the (slow) LLM if forced OR some rewrite file is missing.
            # `all(p.exists() for p in ...)` is True only when every file is there.
            if force or not all(p.exists() for p in rewrite_targets):
                for v in _make_rewrites(seed_rec, project_id):
                    target = out_dir / f"{v['project']['project_id']}.json"
                    # Write each variant to disk immediately (crash-safe).
                    target.write_text(
                        json.dumps(v, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    stats["rewrites_written"] += 1
            else:
                print(f"  [{project_id}] rewrites cached, skipping")

        # --- programmatic positive variants (all enabled axes) ---
        for label in positive_labels:
            target = out_dir / f"{project_id}__pos_{label}.json"
            if target.exists() and not force:
                continue   # already generated on a previous run — skip
            variants = make_positive_variants(seed_rec, [label])
            if not variants:
                continue   # this axis didn't apply to this seed
            target.write_text(
                json.dumps(variants[0], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            stats["positives_written"] += 1

        # --- programmatic evaluation negatives (all enabled codes) ---
        for defect_code in negative_codes:
            target = out_dir / f"{project_id}__neg_{defect_code}.json"
            if target.exists() and not force:
                continue   # cached — skip
            neg = make_evaluation_negative(seed_rec, defect_code)
            if neg is None:
                continue   # defect couldn't be injected into this seed
            target.write_text(
                json.dumps(neg, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            stats["negatives_written"] += 1

    return stats
