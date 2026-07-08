"""Gate tests for merge_adapter.py's pure (no-GPU) pieces.

Runnable two ways:
    pytest tests/test_merge_adapter.py
    python tests/test_merge_adapter.py     # no pytest needed
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from merge_adapter import card_sources, inference_generation_config  # noqa: E402

# The stock Qwen2.5-3B-Instruct generation_config that save_pretrained copies
# into the merged dir — the exact dict that caused invalid-JSON output when
# the export was loaded with defaults.
QWEN_STOCK_GENCFG = {
    "bos_token_id": 151643,
    "do_sample": True,
    "eos_token_id": [151645, 151643],
    "pad_token_id": 151643,
    "repetition_penalty": 1.05,
    "temperature": 0.7,
    "top_k": 20,
    "top_p": 0.8,
    "transformers_version": "5.5.0",
}


def test_gencfg_forces_greedy():
    cfg = inference_generation_config(QWEN_STOCK_GENCFG)
    assert cfg["do_sample"] is False


def test_gencfg_drops_every_sampling_knob():
    cfg = inference_generation_config(QWEN_STOCK_GENCFG)
    for knob in ("temperature", "top_p", "top_k"):
        assert knob not in cfg, f"{knob} must not ship in the export"


def test_gencfg_keeps_token_ids():
    cfg = inference_generation_config(QWEN_STOCK_GENCFG)
    assert cfg["bos_token_id"] == 151643
    assert cfg["eos_token_id"] == [151645, 151643]
    assert cfg["pad_token_id"] == 151643


def test_gencfg_sets_card_recommended_repetition_penalty():
    cfg = inference_generation_config(QWEN_STOCK_GENCFG)
    assert cfg["repetition_penalty"] == 1.1


def test_gencfg_empty_base_still_valid():
    # gc file missing in the merged dir -> still ships a greedy config
    cfg = inference_generation_config({})
    assert cfg == {"do_sample": False, "repetition_penalty": 1.1}


def test_exported_gencfg_is_greedy_if_present():
    # Guard the real artifact: if out/parti-base has been exported, its
    # generation_config must be the greedy one — never the base model's
    # sampling defaults (do_sample=true, temp 0.7), which caused invalid
    # JSON for anyone loading the export as-is.
    import json
    gc = Path(__file__).resolve().parent.parent / "out" / "parti-base" \
        / "generation_config.json"
    if not gc.exists():
        return  # nothing exported yet — nothing to guard
    cfg = json.loads(gc.read_text(encoding="utf-8"))
    assert cfg.get("do_sample") is False
    for knob in ("temperature", "top_p", "top_k"):
        assert knob not in cfg


def test_card_sources_only_existing(tmp_path=None):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        old = Path(d)
        assert card_sources(old) == []
        (old / "README.md").write_text("card", encoding="utf-8")
        assert card_sources(old) == [old / "README.md"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"{len(fns)} passed")
