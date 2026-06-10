"""Offline smoke test for the DatasetGen pipeline (no Ollama / no LLM).

Run:  python selfcheck.py

Exercises every stage that doesn't need the model:
  1. all modules import
  2. normalize + validate the raw corpus
  3. programmatic positive variants pass the validator by construction
  4. programmatic evaluation negatives fail with their labelled defect code
  5. Stage-4 row generation produces valid ChatML for every mode
  6. existing out/pilot.jsonl (if present) has well-formed records

Exit code 0 = all pass, 1 = something failed.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str):
    def deco(fn):
        try:
            detail = fn()
            results.append((PASS, name, detail or ""))
        except Exception as e:  # noqa: BLE001 - smoke test wants the message
            results.append((FAIL, name, f"{type(e).__name__}: {e}"))
        return fn
    return deco


@check("modules import")
def _imports():
    import synth.config, synth.corpus, synth.normalize, synth.validate  # noqa
    import synth.fixup, synth.staged, synth.assemble, synth.denormalize  # noqa
    import synth.programmatic_variants, synth.phase_variants  # noqa
    import synth.semantic_audit, synth.ollama_client, synth.costs  # noqa
    return "13 modules"


@check("normalize + validate raw corpus")
def _normalize():
    from synth.corpus import iter_configs
    from synth.normalize import normalize_seed
    from synth.validate import validate_normalized
    clean = flagged = 0
    for slug, raw in iter_configs():
        rec = normalize_seed(slug, raw)
        errs = [i for i in validate_normalized(rec) if i["severity"] == "error"]
        if errs:
            flagged += 1
        else:
            clean += 1
    if clean == 0:
        raise AssertionError("no clean seeds — normalizer broken")
    return f"{clean} clean, {flagged} flagged"


def _a_clean_seed() -> dict:
    """Build one valid normalized seed from the corpus (no out/ dependency)."""
    from synth.corpus import iter_configs
    from synth.normalize import normalize_seed
    from synth.fixup import fixup_record
    from synth.validate import is_valid
    for slug, raw in iter_configs():
        rec = normalize_seed(slug, raw)
        if not is_valid(rec):
            rec, _ = fixup_record(rec)
        if is_valid(rec):
            return rec
    raise AssertionError("no clean seed could be built from the corpus")


@check("programmatic positive variants validate")
def _positives():
    from synth.programmatic_variants import make_positive_variants, PROGRAMMATIC_POSITIVE_AXES
    from synth.validate import is_valid
    seed = _a_clean_seed()
    ok = total = 0
    for label in PROGRAMMATIC_POSITIVE_AXES:
        total += 1
        v = make_positive_variants(seed, [label])
        if v and is_valid(v[0]):
            ok += 1
    if ok == 0:
        raise AssertionError("no positive variant validated")
    return f"{ok}/{total} axes valid (some may skip per seed)"


@check("programmatic negatives fail as labelled")
def _negatives():
    from synth.programmatic_variants import make_evaluation_negative, PROGRAMMATIC_NEGATIVE_DEFECTS
    from synth.validate import validate_normalized
    seed = _a_clean_seed()
    ok = total = 0
    for code in PROGRAMMATIC_NEGATIVE_DEFECTS:
        total += 1
        n = make_evaluation_negative(seed, code)
        if n is None:
            continue
        errs = [e for e in validate_normalized(n) if e["severity"] == "error"]
        if any(e["code"] == code for e in errs):
            ok += 1
    if ok != total:
        raise AssertionError(f"only {ok}/{total} negatives flagged with their code")
    return f"{ok}/{total} defects labelled"


@check("Stage-4 produces valid ChatML")
def _staged():
    from synth.staged import iter_rows, MODE_GENERATORS
    from synth.assemble import to_chatml
    recs = [_a_clean_seed()]
    modes_seen = set()
    count = 0
    for system, user, asst, mode in iter_rows(recs):
        rec = to_chatml(system, user, asst)
        assert [m["role"] for m in rec["messages"]] == ["system", "user", "assistant"]
        json.loads(asst)  # assistant turn must be valid JSON
        modes_seen.add(mode)
        count += 1
    missing = set(MODE_GENERATORS) - modes_seen
    if missing:
        raise AssertionError(f"modes never emitted: {missing}")
    return f"{count} rows across modes {sorted(modes_seen)}"


@check("existing pilot.jsonl integrity")
def _pilot():
    p = ROOT / "out" / "pilot.jsonl"
    if not p.exists():
        return "skipped (no pilot.jsonl yet)"
    ok = bad = 0
    for line in p.open(encoding="utf-8"):
        rec = json.loads(line)
        roles = [m["role"] for m in rec["messages"]]
        assert roles == ["system", "user", "assistant"], f"bad roles {roles}"
        try:
            json.loads(rec["messages"][-1]["content"])
            ok += 1
        except json.JSONDecodeError:
            bad += 1
    if bad:
        raise AssertionError(f"{bad} assistant turns are not valid JSON")
    return f"{ok} records, all assistant turns valid JSON"


def main() -> int:
    print("=== DatasetGen self-check (offline, no LLM) ===\n")
    for status, name, detail in results:
        mark = "[PASS]" if status == PASS else "[FAIL]"
        line = f"  {mark} {name}"
        if detail:
            line += f"  - {detail}"
        print(line)
    failed = [r for r in results if r[0] == FAIL]
    print()
    if failed:
        print(f"FAILED ({len(failed)}/{len(results)})")
        return 1
    print(f"ALL PASSED ({len(results)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
