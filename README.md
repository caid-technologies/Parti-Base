# DatasetGen — synthesize an SFT dataset for hobbyist project design

This pipeline turns 42 hobbyist electronics/manufacturing project examples
under [Data/](Data/) into both:

1. **`out/pilot.jsonl`** — ChatML SFT dataset covering six task modes (A–F)
2. **`out/dataset/`** — 275 project folders in the same 5-file format as the input

The canonical schema and behavior contract are defined in [CLAUDE.md](CLAUDE.md).

## Pipeline overview

Four stages. Local model served by Ollama (default: `qwen3-coder:30b`).

```
Data/                                          Stage 1 (offline, deterministic)
  *_CONFIG.json + GUIDE.md + CSV    ─────►   synth/normalize.py
                                              ▼
out/normalized/<slug>.json                     Stage 2 (offline, schema check)
  canonical CLAUDE.md schema       ─────►   synth/validate.py
                                              ▼
out/variants/<id>.json                         Stage 3 (hybrid)
  prompt rewrites (LLM)            ─────►   synth/phase_variants.py + LLM
  positive variants (programmatic) ─────►   synth/programmatic_variants.py
  evaluation negatives (programmatic)           ▼
                                              Stage 4 (offline, projection)
                                              synth/staged.py — Mode A–F
                                              synth/assemble.py — ChatML wrap
                                              ▼
out/pilot.jsonl                                ChatML SFT dataset
                                              + (optional)
                                              build_dataset.py
                                              synth/denormalize.py
                                              ▼
out/dataset/<id>_files/                        5-file source-format bundles
```

## Output format 1 — ChatML JSONL (`out/pilot.jsonl`)

Six task modes per CLAUDE.md spec:

| Mode | Task | User turn | Assistant turn |
|---|---|---|---|
| A | Normalize | "Normalize the following hardware project…" + prompt | full canonical record |
| B | Prompt→Project | raw project prompt | full canonical record |
| C | Prompt→Components | raw project prompt | `{"components": [...]}` |
| D | Components→Relationships | components table | `{"relationships": [...]}` |
| E | Project→Instructions | `{project, components, relationships}` | `{"instructions": [...]}` |
| F | Project→Validation | record with `validation` blanked | full `validation` block |

Per-mode system prompts live in [synth/staged.py](synth/staged.py).

Sample record:
```jsonc
{
  "messages": [
    {"role": "system",    "content": "Mode B — Prompt→Project. You design hobbyist..."},
    {"role": "user",      "content": "DIY a medium size digital clock..."},
    {"role": "assistant", "content": "{ \"project\": {...}, \"components\": [...], ... }"}
  ]
}
```

## Output format 2 — folder-per-project (`out/dataset/`)

Same 5-file structure as the input `Data/`:

```
out/dataset/<project_id>_files/
  <project_id>_CONFIG.json
  <project_id>_GUIDE.md
  <project_id>_MECHANICAL_CONNECTIONS.json
  <project_id>_ELECTRICAL_CONNECTIONS.json
  <project_id>_PARTS.csv
```

275 folders total: 42 seeds + 233 variants (117 prompt rewrites + 76 positive
variants + 40 evaluation negatives). PNG generation is left as a separate
downstream concern.

## Setup

### 1. Install Ollama (one-time, native Windows)

Download from [ollama.com/download](https://ollama.com/download). The service
starts automatically on `localhost:11434`.

```powershell
ollama --version
curl http://localhost:11434/v1/models
```

### 2. Pull the model (only needed for Stage 3 LLM rewrites)

```powershell
ollama pull qwen3-coder:30b
# MoE model: 30B total, ~3B active per token. Strong structured-JSON output.
# Other good picks: qwen2.5-coder:14b-instruct-q4_K_M (smaller, fits VRAM fully)
```

Stages 1, 2, and 4 don't call Ollama. Stage 3 calls it for LLM prompt
rewrites; positives and evaluation negatives are produced programmatically
without LLM calls.

### 3. Python deps + env

```powershell
conda create -n datagen python=3.11 -y
conda activate datagen
pip install -r requirements.txt
# Edit .env to set MODEL_ID=qwen3-coder:30b (or whatever you pulled)
```

## Run

### Dry-run (project counts, no files written)

```powershell
python run.py --dry-run
```

### Generate the ChatML pilot (Stages 1, 2, 4 — no LLM)

```powershell
python run.py
```

Stage 1 runs automatically if `out/normalized/` is missing or incomplete.
Stage 4 produces `out/pilot.jsonl` (~250 rows from 42 seeds across all modes).

### Generate with Stage 3 variants (LLM rewrites + programmatic positives/negatives)

```powershell
python run.py --enable-variants
```

Adds ~233 variant records, bumping the pilot to ~1080 rows. The LLM rewrites
take ~30 sec per seed (~18 min for 36 seeds); programmatic variants are
sub-second.

### Build the folder-format dataset

```powershell
python build_dataset.py
```

Projects every record in `out/normalized/` + `out/variants/` into the 5-file
source format under `out/dataset/`. Pure-Python — runs in seconds.

CLI options:
- `python build_dataset.py --seeds-only` — skip variants, just the 42 seeds
- `python build_dataset.py --out path` — alternate output directory

### Standalone Stage 1 with issue analytics

```powershell
python normalize_all.py
python normalize_all.py --summary-only   # stats only, don't write files
```

Useful when you want to inspect the normalization issue distribution without
running the rest of the pipeline.

### Useful run.py flags

- `--modes ABCDEF` — pick which modes to emit (e.g. `--modes BF`)
- `--enable-variants` — run Stage 3 (LLM rewrites + programmatic mutations)
- `--force-variants` — regenerate cached variants
- `--variant-seeds-limit N` — cap seeds for smoke tests
- `--force-normalize` — re-run Stage 1 from scratch
- `--seed N` — deterministic shuffling
- `--out path` — write somewhere else
- `--dry-run` — project counts only

### Zero-shot base-model test cases (txt + hand-drawn sketch inputs)

`testcases.py` measures how an UNTRAINED base model handles the core use case
(document → full canonical record). Default media per seed project: the
original prompt as `.txt`, and an image of the product sent as a vision
content part. Image source priority: a hand-drawn sketch dropped into
`Data/sketches/<slug>.png` (`.jpg`/`.jpeg`/`.webp` also work) wins when
present; otherwise the project's `VISUAL.png` render is used, and each case
records `image_source: sketch|render`. `Data/sketches/PRODUCTS.md` lists the
42 products to draw for the sketch transition. `--types` can add `md`
(GUIDE.md verbatim) and `pdf` (guide rendered to PDF, text re-extracted with
pypdf at run time). Gold is `out/normalized/<slug>.json`; scoring reuses
`eval_local.py` (parse rate, strict-schema valid rate, structural F1). This
is the no-training baseline the fine-tuned adapter must beat.

```powershell
python testcases.py build                    # deterministic, no LLM — writes out/testcases/
python testcases.py run --model qwen3.5      # zero-shot eval via Ollama
python testcases.py run --types txt --per-type 5          # cheap smoke
python testcases.py build --types txt,md,pdf,image        # include the doc media
```

`run` prints a per-input-type table and writes
`out/testcases/report_<model>.json`. Image cases require a vision-capable
Ollama tag; on a text-only model they are recorded as call errors, not
crashes. Gate tests: `pytest tests/test_testcases.py` (no LLM calls).

### Inspect ChatML output

```powershell
# First record (pretty-printed)
Get-Content out/pilot.jsonl -TotalCount 1 | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Per-mode counts
python -c "
import json
from collections import Counter
c = Counter()
for line in open('out/pilot.jsonl', encoding='utf-8'):
    sys_msg = json.loads(line)['messages'][0]['content']
    for m in 'ABCDEF':
        if f'Mode {m}' in sys_msg:
            c[m] += 1; break
print(dict(c))
"
```

## Project layout

```
Data/                          raw input — 42 project folders
CLAUDE.md                      canonical schema + behavior contract
synth/
  config.py                    env-driven settings, paths
  corpus.py                    load raw CONFIG.json files
  normalize.py                 raw → canonical schema (Stage 1)
  validate.py                  canonical-schema validator (Stage 2)
  ollama_client.py             OpenAI-compatible client (Stage 3 LLM use)
  phase_variants.py            Stage 3 orchestrator (LLM rewrites)
  programmatic_variants.py     Stage 3 deterministic positives + negatives
  staged.py                    Mode A–F row generators (Stage 4)
  assemble.py                  ChatML wrap + dedup + shuffle (Stage 4)
  denormalize.py               canonical record → 5-file source bundle
run.py                         end-to-end orchestrator (Stages 1 + 3 + 4)
build_dataset.py               canonical records → out/dataset/ folders
normalize_all.py               standalone Stage 1 with issue analytics
out/
  normalized/<slug>.json       Stage 1 output
  variants/<id>.json           Stage 3 output
  pilot.jsonl                  Stage 4 output (ChatML dataset)
  dataset/<id>_files/          build_dataset.py output (folder bundles)
```

## Stage 3 implementation notes

Initial design was full-LLM variant generation. A smoke test on Nemotron3:33b
showed the canonical schema is too deep for Ollama's `format` mode to reliably
enforce — positive variants failed with 30–60 schema violations per attempt
and 0 of 6 variants accepted in 91 minutes of generation. The current pivot:

- **Prompt rewrites** — LLM only. Small output (~3 short strings),
  schema is trivial; any 7B+ model handles it. On `qwen3-coder:30b` (MoE,
  ~3B active per token) this lands in ~10 sec per seed.
- **Positive variants** — programmatic Python transforms over the canonical
  record. Five axes: `compact`, `standard_size`, `low_cost`, `premium_material`,
  `accessory_light`. Each is a deterministic scale/swap/drop operation; passes
  the strict validator by construction. Sub-second per variant.
- **Evaluation negatives** — programmatic defect injection. Four defect codes:
  `dangling_ref`, `invalid_component_type`, `invalid_relation`,
  `dangling_step_ref`. Each crafts a record that fails strict validation in a
  known way, with the matching issue flagged in `validation.issues[]`.

With Qwen3-Coder's stronger schema discipline, LLM positive variants might
become viable again — worth re-testing if you want more creative mutations
than the 5 programmatic axes offer. The path is preserved in git history.

## Reusing the same Ollama server for RAG

Ollama is a persistent background service. Any other project — including a
future RAG app — hits the same endpoint:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
resp = client.chat.completions.create(
    model="qwen3-coder:30b",
    messages=[{"role": "user", "content": "Summarize this doc..."}],
)
```

For RAG you'll also want an embedding model — `ollama pull nomic-embed-text`
is a solid default.
