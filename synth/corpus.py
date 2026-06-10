"""Load existing CONFIG.json files and produce normalized training targets."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterator

from .config import DATA_DIR

# Keys we strip from the assistant response. They are corpus-bookkeeping fields
# (ids, image-pipeline cache fingerprints, etc.) that a freshly-trained model
# shouldn't be asked to predict.
DROP_TOP_LEVEL = {"projectId", "imagePromptSnapshot", "wiringCleanedHash", "approach"}

# Node fields stripped from training targets. These are scraped affiliate
# links and cache blobs that would teach the model to hallucinate URLs.
DROP_NODE = {"imageUrl", "purchaseUrl", "ebayUrl", "amazonUrl", "aliexpressUrl",
             "research", "partId"}


def _normalize_node(node: dict) -> dict:
    return {k: v for k, v in node.items() if k not in DROP_NODE}


def _normalize_config(cfg: dict) -> dict:
    out = {k: v for k, v in cfg.items() if k not in DROP_TOP_LEVEL}
    if "nodes" in out:
        out["nodes"] = [_normalize_node(n) for n in out["nodes"]]
    # Canonical key order so downstream diff/dedup is stable.
    canonical_order = [
        "projectName", "projectDescription", "originalPrompt", "notes",
        "plan", "nodes", "electricalConnections", "mechanicalConnections",
        "instructionPreamble", "instructionSteps",
    ]
    ordered = {k: out[k] for k in canonical_order if k in out}
    for k, v in out.items():
        if k not in ordered:
            ordered[k] = v
    return ordered


def iter_configs() -> Iterator[tuple[str, dict]]:
    """Yield (project_slug, normalized_config) for every project folder."""
    for folder in sorted(DATA_DIR.iterdir()):
        if not folder.is_dir():
            continue
        matches = list(folder.glob("*_CONFIG.json"))
        if not matches:
            continue
        cfg_path: Path = matches[0]
        slug = folder.name.removesuffix("_files")
        with cfg_path.open(encoding="utf-8") as f:
            raw = json.load(f)
        yield slug, _normalize_config(raw)
