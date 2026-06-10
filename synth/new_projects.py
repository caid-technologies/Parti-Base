"""Generate brand-new projects with the LLM, grounded in the Data/ corpus.

Strategy that avoids the deep-schema failure mode:
  1. Few-shot the model with 1-2 REAL raw-CONFIG files from Data/.
  2. Ask it to invent a NEW project in that same flat raw-CONFIG format
     (projectName, originalPrompt, nodes, electricalConnections,
     mechanicalConnections, instructionSteps).
  3. Run the output through the existing normalize → fixup → validate
     pipeline, which already handles the raw format robustly.
  4. Accept if it passes strict validation; reject + log otherwise.

The raw format is flat and the model has 42 examples of it, so generation is
far more reliable than asking for the deep canonical schema directly.
"""
from __future__ import annotations
import json
import random
from collections.abc import Iterator
from pathlib import Path

from .config import DATA_DIR
from .corpus import iter_configs
from .fixup import backfill_print_settings, fixup_record
from .normalize import normalize_seed, to_snake_id
from .ollama_client import chat_json
from .briefs import ALL_BRIEFS
from .validate import is_valid, validate_normalized

# Domain prompts to steer ideation toward fresh concepts (not corpus clones).
NEW_PROJECT_BRIEFS = ALL_BRIEFS

# Two projects whose signatures overlap by more than this Jaccard ratio are
# considered near-duplicates; the newer one is rejected.
SIMILARITY_THRESHOLD = 0.55

_STOPWORDS = {
    "a", "an", "the", "with", "and", "for", "of", "to", "in", "on", "via",
    "system", "module", "controller", "kit", "device", "unit", "mini",
    "small", "portable", "desktop", "smart", "custom", "main", "board",
}


# Light schema to keep the raw output well-formed without over-constraining.
RAW_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["projectName", "originalPrompt", "nodes",
                 "electricalConnections", "mechanicalConnections",
                 "instructionSteps"],
    "properties": {
        "projectName": {"type": "string", "minLength": 3},
        "originalPrompt": {"type": "string", "minLength": 20},
        "projectDescription": {"type": "string"},
        "nodes": {
            "type": "array",
            "minItems": 4,
            "items": {
                "type": "object",
                "required": ["id", "name", "type", "category", "quantity",
                             "estimatedCost", "description"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "category": {"type": "string"},
                    "quantity": {"type": "integer", "minimum": 1},
                    "estimatedCost": {"type": "number", "minimum": 0},
                    "description": {"type": "string"},
                    "dimensions": {"type": "string"},
                    "material": {"type": "string"},
                    "productName": {"type": "string"},
                    "printSettings": {"type": "string"},
                },
            },
        },
        "electricalConnections": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target"],
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "type": {"type": "string"},
                    "voltage": {"type": "string"},
                    "protocol": {"type": "string"},
                    "sourcePin": {"type": "string"},
                    "targetPin": {"type": "string"},
                },
            },
        },
        "mechanicalConnections": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["label", "source", "target"],
                "properties": {
                    "label": {"type": "string"},
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                },
            },
        },
        "instructionSteps": {
            "type": "array",
            "minItems": 2,
            "items": {
                "type": "object",
                "required": ["id", "subSteps"],
                "properties": {
                    "id": {"type": "string"},
                    "subSteps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "title", "partIds"],
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "partIds": {"type": "array",
                                            "items": {"type": "string"}},
                            },
                        },
                    },
                },
            },
        },
    },
}


def _load_raw_exemplars() -> list[tuple[str, dict]]:
    """Load raw (un-normalized) CONFIG dicts straight from Data/."""
    out: list[tuple[str, dict]] = []
    for folder in sorted(DATA_DIR.iterdir()):
        if not folder.is_dir():
            continue
        matches = list(folder.glob("*_CONFIG.json"))
        if not matches:
            continue
        raw = json.loads(matches[0].read_text(encoding="utf-8"))
        out.append((folder.name.removesuffix("_files"), raw))
    return out


def _trim_exemplar(raw: dict) -> dict:
    """Shrink a raw CONFIG to keep few-shot context manageable."""
    trimmed_nodes = []
    for n in raw.get("nodes", [])[:12]:
        trimmed_nodes.append({
            k: n[k] for k in
            ("id", "name", "type", "category", "quantity", "estimatedCost",
             "description", "dimensions", "material")
            if k in n
        })
    return {
        "projectName": raw.get("projectName", ""),
        "originalPrompt": raw.get("originalPrompt", ""),
        "nodes": trimmed_nodes,
        "electricalConnections": raw.get("electricalConnections", [])[:8],
        "mechanicalConnections": raw.get("mechanicalConnections", [])[:8],
        "instructionSteps": raw.get("instructionSteps", []),
    }


def _build_messages(brief: str, exemplars: list[tuple[str, dict]]) -> list[dict]:
    system = (
        "You are a hardware project designer. You invent buildable hobbyist "
        "electronics + mechanical projects and output them as a single JSON "
        "object in this exact flat format:\n"
        "  projectName, originalPrompt, projectDescription,\n"
        "  nodes[]            (every part: id, name, type, category, "
        "quantity, estimatedCost, description, dimensions, material),\n"
        "  electricalConnections[] (source, target, type, voltage, protocol, "
        "sourcePin, targetPin),\n"
        "  mechanicalConnections[] (label, source, target),\n"
        "  instructionSteps[]  (id is one of fabricate/wire/bringup/assemble; "
        "each has subSteps[] with id, title, partIds).\n\n"
        "Hard rules:\n"
        "  - Every node id is snake_case ASCII.\n"
        "  - Every connection source/target and every partIds entry MUST be "
        "an id that exists in nodes.\n"
        "  - WIRING IS MANDATORY: every electrical node (sensor, MCU, display, "
        "module, power, LED, button) must appear in at least one "
        "electricalConnections entry. Wire peripherals to the controller in a "
        "star: each peripheral has a connection with source=<controller_id>, "
        "target=<peripheral_id>. An electrical project with an empty or partial "
        "electricalConnections array is invalid and will be discarded.\n"
        "  - Use real, commonly-available parts (ESP32, BME280, NEMA17, "
        "TP4056, etc.). Do not invent fake product names.\n"
        "  - originalPrompt is what a hobbyist would type to request this "
        "build — natural language, first person.\n"
        "  - If the prompt mentions a feature (remote, speaker, battery, "
        "wifi), include a node that provides it.\n"
        "  - Output ONLY the JSON object."
    )
    ex_text = "\n\n".join(
        f"=== Example: {slug} ===\n{json.dumps(_trim_exemplar(raw), indent=2)[:4000]}"
        for slug, raw in exemplars
    )
    user = (
        f"Reference examples of the format:\n\n{ex_text}\n\n"
        f"=== Now invent a NEW project ===\n"
        f"Concept: {brief}\n\n"
        f"Produce a complete, internally-consistent design as one JSON object. "
        f"Make it genuinely different from the examples."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _signature(rec: dict) -> set[str]:
    """A bag-of-tokens fingerprint of a project's identity.

    Built from the project name + component display names + functional roles.
    Two projects with high token overlap describe basically the same build.
    """
    tokens: set[str] = set()
    name = rec.get("project", {}).get("name", "")
    for t in name.lower().replace("-", " ").replace("/", " ").split():
        if t not in _STOPWORDS and len(t) > 2:
            tokens.add(t)
    for c in rec.get("components", []):
        role = (c.get("functional_role") or "").lower()
        if role and role != "unknown":
            tokens.add(f"role:{role}")
        for t in (c.get("display_name") or "").lower().split():
            t = t.strip("()-.,")
            if t and t not in _STOPWORDS and len(t) > 2:
                tokens.add(t)
    return tokens


def _max_similarity(sig: set[str], existing: list[set[str]]) -> float:
    """Highest Jaccard similarity of `sig` against any existing signature."""
    best = 0.0
    for other in existing:
        if not sig or not other:
            continue
        inter = len(sig & other)
        if inter == 0:
            continue
        jac = inter / len(sig | other)
        if jac > best:
            best = jac
    return best


def load_existing_signatures(normalized_dir: Path) -> list[set[str]]:
    """Signatures for every project already in `normalized_dir`."""
    sigs: list[set[str]] = []
    for p in normalized_dir.glob("*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        sigs.append(_signature(rec))
    return sigs


# Models often emit connection keys with natural names instead of the corpus
# convention. Ollama's guided decoding is a hint, not strict enforcement, so we
# remap these aliases before normalization. Without this, every connection is
# read as a dangling reference and dropped → 0 relationships.
_CONN_KEY_ALIASES = {
    "from": "source",
    "to": "target",
    "src": "source",
    "dst": "target",
    "dest": "target",
    "from_id": "source",
    "to_id": "target",
    "pin_from": "sourcePin",
    "pin_to": "targetPin",
    "from_pin": "sourcePin",
    "to_pin": "targetPin",
    "sourcepin": "sourcePin",
    "targetpin": "targetPin",
}


def _canonicalize_connection_keys(raw: dict) -> None:
    """In-place remap of connection key aliases (from/to → source/target)."""
    for arr_key in ("electricalConnections", "mechanicalConnections"):
        for conn in raw.get(arr_key, []):
            if not isinstance(conn, dict):
                continue
            for alias, canonical in _CONN_KEY_ALIASES.items():
                if alias in conn and canonical not in conn:
                    conn[canonical] = conn.pop(alias)


def generate_one(
    brief: str,
    exemplars: list[tuple[str, dict]],
    rng: random.Random,
) -> tuple[dict, list[str]] | None:
    """Generate + normalize + fixup + validate one new project.

    Returns (normalized_record, actions) on success, None on failure.
    """
    sample = rng.sample(exemplars, k=min(2, len(exemplars)))
    messages = _build_messages(brief, sample)
    try:
        raw = chat_json(messages, schema=RAW_CONFIG_SCHEMA,
                        temperature=0.8, max_tokens=12000)
    except Exception as e:  # noqa: BLE001
        print(f"  [new] generate failed for {brief!r}: {e}")
        return None

    if not isinstance(raw, dict):
        print(f"  [new] rejected {brief!r}: model returned non-object")
        return None

    # Everything below processes untrusted LLM output. Any malformed structure
    # must REJECT this one sample, never crash the whole (multi-hour) run.
    try:
        _canonicalize_connection_keys(raw)
        name = raw.get("projectName") or brief
        slug = "new_" + to_snake_id(str(name))[:48]
        rec = normalize_seed(slug, raw)
        actions: list[str] = []
        if not is_valid(rec):
            rec, actions = fixup_record(rec)
        if not is_valid(rec):
            errs = [i["code"] for i in validate_normalized(rec)
                    if i["severity"] == "error"]
            print(f"  [new] rejected {slug!r}: {errs[:4]}")
            return None
    except Exception as e:  # noqa: BLE001
        print(f"  [new] rejected {brief!r}: malformed output ({type(e).__name__}: {e})")
        return None

    # Generated configs rarely include printSettings; backfill defaults so the
    # fabrication structure matches the Data examples.
    n_fab = backfill_print_settings(rec)
    if n_fab:
        actions.append(f"backfill {n_fab} print settings")

    rec["project"]["variant_type"] = "seed"
    rec["project"]["seed_project_id"] = rec["project"]["project_id"]
    rec["project"]["visual_ref"] = None  # no image for synthetic projects
    rec["project"]["synthetic"] = True
    return rec, actions


def generate_new_projects(
    out_dir: Path,
    count: int,
    seed: int = 0,
    briefs: list[str] | None = None,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
) -> dict:
    """Generate `count` new validated, distinct projects into out_dir.

    Rejects any project too similar (Jaccard >= `similarity_threshold`) to an
    existing project OR to one already accepted this run, so scaling up adds
    real diversity instead of near-duplicates.
    """
    rng = random.Random(seed)
    exemplars = _load_raw_exemplars()
    out_dir.mkdir(parents=True, exist_ok=True)
    pool = list(briefs or NEW_PROJECT_BRIEFS)
    rng.shuffle(pool)

    # Seed the dedup set with everything already on disk.
    signatures = load_existing_signatures(out_dir)

    accepted = 0
    attempts = 0
    invalid_rejects = 0
    similar_rejects = 0
    max_attempts = count * 5
    i = 0
    while accepted < count and attempts < max_attempts:
        brief = pool[i % len(pool)]
        i += 1
        attempts += 1
        result = generate_one(brief, exemplars, rng)
        if result is None:
            invalid_rejects += 1
            continue
        rec, actions = result

        sig = _signature(rec)
        sim = _max_similarity(sig, signatures)
        if sim >= similarity_threshold:
            similar_rejects += 1
            print(f"  [new] rejected (similar {sim:.2f}) "
                  f"{rec['project']['project_id']}")
            continue

        pid = rec["project"]["project_id"]
        target = out_dir / f"{pid}.json"
        if target.exists():
            continue  # filename collision, skip
        target.write_text(json.dumps(rec, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        signatures.append(sig)
        accepted += 1
        note = f" (fixup: {len(actions)})" if actions else ""
        print(f"  [new] accepted {pid} (distinct, sim {sim:.2f}){note}")

    return {
        "accepted": accepted,
        "attempts": attempts,
        "invalid_rejects": invalid_rejects,
        "similar_rejects": similar_rejects,
        "reject_rate": round(1 - accepted / max(attempts, 1), 2),
    }
