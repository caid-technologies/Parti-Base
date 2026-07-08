"""Merge the trained LoRA adapter into a full fp16 model — CPU only.

The merged safetensors under out/blueprint-qwen3b went stale: they were
written on an earlier training run, while out/lora/adapter has since been
retrained. This script produces a FRESH merged model from the current
adapter without touching the GPU (which may be busy training/serving):

    base   Qwen/Qwen2.5-3B-Instruct  (fp16, downloaded/cached from HF)
    + LoRA out/lora/adapter          (the latest checkpoint promotion)
    ->     out/parti-base/           (merged fp16 safetensors + tokenizer)

The adapter was TRAINED against the 4-bit unsloth base, but LoRA weights
attach by module name, so merging into the full-precision twin is the
standard unsloth-recommended export path (no quantization error baked in).

Run (any env with torch+peft+transformers, e.g. unsloth):
    python merge_adapter.py                 # merge + 20-token smoke
    python merge_adapter.py --skip-smoke    # merge only
    python merge_adapter.py --out other_dir
"""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ADAPTER = ROOT / "out" / "lora" / "adapter"
OUT = ROOT / "out" / "parti-base"
BASE = "Qwen/Qwen2.5-3B-Instruct"

# Model-card / doc files worth carrying over from the old merged dir if they
# exist (weights and tokenizer are NOT in this list on purpose — those must
# come from the fresh merge, never the stale folder).
CARD_FILES = ("README.md",)


def card_sources(old_dir: Path) -> list[Path]:
    """Pure helper: which doc files to copy from the previous merged dir."""
    return [old_dir / n for n in CARD_FILES if (old_dir / n).exists()]


# Token-id keys worth keeping from the base model's generation_config; every
# sampling knob is dropped on purpose (see inference_generation_config).
_GENCFG_KEEP = ("bos_token_id", "eos_token_id", "pad_token_id",
                "transformers_version")


def inference_generation_config(base_cfg: dict) -> dict:
    """Pure helper: the generation_config the merged export must ship.

    save_pretrained copies the BASE model's generation_config, and Qwen2.5-
    Instruct's stock one samples (do_sample=true, temp 0.7, top_p 0.8). The
    fine-tune's quality numbers were measured greedy (eval_local.py passes
    do_sample=False), and sampling at 0.7 measurably breaks the JSON output —
    so anyone loading the export with defaults gets a worse model than we
    shipped. Keep the token ids, drop every sampling knob, force greedy plus
    the repetition penalty the model card recommends for wiring lists.
    """
    cfg = {k: base_cfg[k] for k in _GENCFG_KEEP if k in base_cfg}
    cfg["do_sample"] = False
    cfg["repetition_penalty"] = 1.1
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adapter", type=Path, default=ADAPTER)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--skip-smoke", action="store_true",
                    help="skip the 20-token CPU generation sanity check")
    args = ap.parse_args()

    if not args.adapter.exists():
        print(f"No adapter at {args.adapter} — run train_local.py first.")
        return 1
    cfg = json.loads((args.adapter / "adapter_config.json")
                     .read_text(encoding="utf-8"))
    print(f"adapter base: {cfg.get('base_model_name_or_path')}")
    print(f"merging into fp16 twin: {args.base}  (CPU only)")

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map="cpu",
        low_cpu_mem_usage=True,
    )
    model = PeftModel.from_pretrained(base, str(args.adapter),
                                      device_map="cpu")
    model = model.merge_and_unload()
    print("merged; saving...")

    args.out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.out), safe_serialization=True)
    # Tokenizer travels from the ADAPTER dir — train_local.py saved it there,
    # chat template included, and it's what the fine-tune actually used.
    tok = AutoTokenizer.from_pretrained(str(args.adapter))
    tok.save_pretrained(str(args.out))
    for src in card_sources(ROOT / "out" / "blueprint-qwen3b"):
        shutil.copy2(src, args.out / src.name)

    # Replace the inherited generation_config with the greedy inference one.
    gc_path = args.out / "generation_config.json"
    base_cfg = json.loads(gc_path.read_text(encoding="utf-8")) \
        if gc_path.exists() else {}
    gc_path.write_text(
        json.dumps(inference_generation_config(base_cfg), indent=2) + "\n",
        encoding="utf-8")
    print(f"saved -> {args.out}")

    if not args.skip_smoke:
        print("smoke: 20 tokens on CPU (takes ~a minute)...")
        msgs = [{"role": "user", "content": "Design a small LED desk lamp."}]
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                      return_tensors="pt")
        out = model.generate(ids, max_new_tokens=20, do_sample=False,
                             pad_token_id=tok.eos_token_id)
        text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
        print(f"smoke output: {text!r}")
        if not text.strip():
            print("FAIL: empty generation from merged model")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
