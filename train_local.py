"""Local Unsloth QLoRA fine-tune on out/train/*.jsonl — tuned for RTX 4070 (12 GB).

Run inside the `unsloth` conda env, with Ollama stopped to free VRAM:
    conda activate unsloth
    ollama stop qwen3-coder:30b
    python train_local.py

Outputs:
    out/lora/                 trainer checkpoints
    out/lora/adapter/         the LoRA adapter (load on top of the base model)
    out/blueprint-qwen3b/     q4_k_m GGUF for Ollama (see notes if this step fails)

----------------------------------------------------------------------------
v2 training loop — changes driven by the held-out eval (eval_local.py):

  finding                                  -> change
  A/B lost 56% of rows at MAX_SEQ=4096     -> MAX_SEQ=6144 (keeps ~99%)
  train mix is 60% E/F (easy modes)        -> per-mode cap rebalances the data
  Mode F target is constant 92% of the     -> cap F hardest so the model can't
    time ("all valid") -> shortcut risk        coast on the boilerplate
  A/B underfit (complex full records)      -> LoRA rank 16 -> 32 (more capacity)
  memorization worry (loss 0.066)          -> NEFTune noise + 1 epoch + early stop
  Mode D greedy-decode repetition loop     -> NOT fixable here; it's a decoding
                                              fix (repetition_penalty at inference)
----------------------------------------------------------------------------
"""
import os
# Reduce fragmentation OOMs on a tight 12 GB budget. Must be set before torch loads.
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import re
import random
from collections import Counter
from pathlib import Path
from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig
from transformers import EarlyStoppingCallback

ROOT = Path(__file__).resolve().parent
TRAIN_DIR = ROOT / "out" / "train"

MAX_SEQ = 8192   # Train seq cap. Measured (Qwen2.5-3B tok) p50=8026, p95=24189.
                 # 8192 keeps ~51% of rows and covers A/B/E/F far better than
                 # 6144 (23%). Training fits 12 GB at 8192 (grad checkpointing).
# Eval is the VRAM bottleneck, not training: HF upcasts full-sequence logits to
# fp32 for the loss (~6 GB for one 10240-token row), which OOM'd the 4070 on the
# first eval pass at step 50. Cap the held-out val rows shorter so eval fits;
# eval_loss stays a valid early-stop signal, just measured on the shorter subset.
EVAL_MAX_SEQ = 6144
MODEL = "unsloth/Qwen2.5-3B-Instruct-bnb-4bit"

# Per-mode row cap on the TRAINING set only (val/test are left whole so the
# benchmark still measures the real mode mix). Modes E/F dominate at ~775 rows
# each while A/B/C/D sit at ~200–275; F's target is a constant "all valid" block
# 92% of the time. Capping the easy/constant modes stops the model from spending
# capacity memorizing boilerplate and forces it onto the hard generative modes.
MODE_CAP = 350

_MODE_RE = re.compile(r"Mode ([A-F])")


def _row_mode(text: str) -> str:
    m = _MODE_RE.search(text)
    return m.group(1) if m else "?"


def rebalance(ds, cap: int, seed: int = 0):
    """Cap each task mode to `cap` rows (random, seeded). Under-cap modes kept whole."""
    by_mode: dict[str, list[int]] = {}
    for i, text in enumerate(ds["text"]):
        by_mode.setdefault(_row_mode(text), []).append(i)
    rng = random.Random(seed)
    keep: list[int] = []
    for mode, idxs in by_mode.items():
        if len(idxs) > cap:
            keep.extend(rng.sample(idxs, cap))
        else:
            keep.extend(idxs)
    return ds.select(sorted(keep))


model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL, max_seq_length=MAX_SEQ, load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    # r=32 (was 16): A/B full-record generation was underfit; more rank gives the
    # adapter capacity for the hard modes. alpha tracks r (Unsloth convention).
    # dropout kept at 0 to preserve Unsloth's fast kernels — generalization comes
    # from NEFTune + 1 epoch + early stopping + the rebalanced data instead.
    model, r=32, lora_alpha=32, lora_dropout=0, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth", random_state=0,
)


def fmt(ex):
    return {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False)}


def fits(ex):
    # Drop rows longer than MAX_SEQ rather than truncate — a cut-off assistant
    # JSON is a bad training target.
    return len(tokenizer(ex["text"]).input_ids) <= MAX_SEQ


def fits_eval(ex):
    # Eval rows must be shorter: the fp32 logit upcast during the eval loss is
    # what OOMs a 12 GB card on long sequences. Cap val at EVAL_MAX_SEQ.
    return len(tokenizer(ex["text"]).input_ids) <= EVAL_MAX_SEQ


train_ds = (load_dataset("json", data_files=str(TRAIN_DIR / "train.jsonl"), split="train")
            .map(fmt).filter(fits))
val_ds = (load_dataset("json", data_files=str(TRAIN_DIR / "val.jsonl"), split="train")
          .map(fmt).filter(fits_eval))

before = Counter(_row_mode(t) for t in train_ds["text"])
train_ds = rebalance(train_ds, MODE_CAP)
after = Counter(_row_mode(t) for t in train_ds["text"])
print(f"train mode mix  before: {dict(sorted(before.items()))}")
print(f"train mode mix  after : {dict(sorted(after.items()))}")
print(f"kept {len(train_ds)} train / {len(val_ds)} val rows (<= {MAX_SEQ} tokens, cap {MODE_CAP}/mode)")

trainer = SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=train_ds, eval_dataset=val_ds,
    args=SFTConfig(
        dataset_text_field="text", max_seq_length=MAX_SEQ,
        # 12 GB only fits batch 1; grad-accum gives an effective batch of 8.
        per_device_train_batch_size=1, gradient_accumulation_steps=8,
        # Eval-OOM guards: batch 1, offload eval tensors to CPU each step, and
        # periodically release cached VRAM to fight fragmentation.
        per_device_eval_batch_size=1, eval_accumulation_steps=1,
        torch_empty_cache_steps=25,
        warmup_ratio=0.03, num_train_epochs=1, learning_rate=2e-4,
        bf16=True,                                  # Ada supports bf16
        # NEFTune: add noise to input embeddings during training. A standard,
        # cheap regularizer that improves instruction-tuning generalization and
        # directly counters the memorization risk flagged by the low train loss.
        neftune_noise_alpha=5,
        logging_steps=10, eval_strategy="steps", eval_steps=50,
        # Keep the best-eval checkpoint, not the last — guards against the
        # memorization we saw (train loss ~0.066 with no eval gate).
        save_strategy="steps", save_steps=50,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss", greater_is_better=False,
        optim="adamw_8bit", weight_decay=0.01, lr_scheduler_type="linear",
        seed=0, output_dir=str(ROOT / "out" / "lora"),
    ),
)
# Mask loss to the assistant turn only — modes E/F have huge JSON *input* turns
# you don't want the model wasting capacity reproducing.
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)
# Stop if eval_loss stops improving — don't keep training into memorization.
trainer.add_callback(EarlyStoppingCallback(early_stopping_patience=3))

trainer.train()

# Save the adapter (always works) ...
model.save_pretrained(str(ROOT / "out" / "lora" / "adapter"))
tokenizer.save_pretrained(str(ROOT / "out" / "lora" / "adapter"))
print("saved LoRA adapter -> out/lora/adapter")

# ... then try the GGUF export for Ollama (most fragile step on Windows; see notes).
try:
    model.save_pretrained_gguf(
        str(ROOT / "out" / "blueprint-qwen3b"), tokenizer,
        quantization_method="q4_k_m",
    )
    print("saved GGUF -> out/blueprint-qwen3b")
except Exception as e:  # noqa: BLE001
    print(f"GGUF export failed ({type(e).__name__}: {e}).")
    print("Training is fine — the adapter is saved. See the GGUF fallback note.")
