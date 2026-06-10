"""Local Unsloth QLoRA fine-tune on out/train/*.jsonl — tuned for RTX 4070 (12 GB).

Run inside the `unsloth` conda env, with Ollama stopped to free VRAM:
    conda activate unsloth
    ollama stop qwen3-coder:30b
    python train_local.py

Outputs:
    out/lora/                 trainer checkpoints
    out/lora/adapter/         the LoRA adapter (load on top of the base model)
    out/blueprint-qwen3b/     q4_k_m GGUF for Ollama (see notes if this step fails)
"""
import os
# Reduce fragmentation OOMs on a tight 12 GB budget. Must be set before torch loads.
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from pathlib import Path
from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

ROOT = Path(__file__).resolve().parent
TRAIN_DIR = ROOT / "out" / "train"

MAX_SEQ = 4096   # drop to 2048 if you OOM on 12 GB; raise on a bigger card
MODEL = "unsloth/Qwen2.5-3B-Instruct-bnb-4bit"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL, max_seq_length=MAX_SEQ, load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=16, lora_dropout=0, bias="none",
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


train_ds = (load_dataset("json", data_files=str(TRAIN_DIR / "train.jsonl"), split="train")
            .map(fmt).filter(fits))
val_ds = (load_dataset("json", data_files=str(TRAIN_DIR / "val.jsonl"), split="train")
          .map(fmt).filter(fits))
print(f"kept {len(train_ds)} train / {len(val_ds)} val rows (<= {MAX_SEQ} tokens)")

trainer = SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=train_ds, eval_dataset=val_ds,
    args=SFTConfig(
        dataset_text_field="text", max_seq_length=MAX_SEQ,
        per_device_train_batch_size=1, gradient_accumulation_steps=8,
        warmup_steps=10, num_train_epochs=2, learning_rate=2e-4,
        logging_steps=10, eval_strategy="steps", eval_steps=50,
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
