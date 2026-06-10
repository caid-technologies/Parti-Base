"""Canonical-schema record → 5-file source bundle.

Mirrors the input format in `Data/` so the synthesized dataset slots in next
to the originals without a format gap:

  <project_id>_files/
    <project_id>_CONFIG.json                  full structured config
    <project_id>_GUIDE.md                     markdown build TOC
    <project_id>_MECHANICAL_CONNECTIONS.json  mechanical relationships only
    <project_id>_ELECTRICAL_CONNECTIONS.json  electrical relationships only
    <project_id>_PARTS.csv                    tabular parts list

Skips VISUAL.png — that's a separate downstream concern.
"""
from __future__ import annotations
import csv
import io
import json
from typing import Any

# --- field-mapping helpers -------------------------------------------------

# canonical phase id → source CONFIG.json instructionSteps phase id
_PHASE_MAP_REVERSE = {
    "fabrication": "fabricate",
    "wiring": "wire",
    "bring_up": "bringup",
    "assembly": "assemble",
    "testing": "test",
}


def _dims_to_string(dims: dict | None) -> str:
    """Rebuild a dimension string from the parsed dict; fall back to raw."""
    if not isinstance(dims, dict):
        return ""
    if dims.get("raw"):
        return str(dims["raw"])
    if "thread" in dims and "length_mm" in dims:
        return f"{dims['thread']}x{dims['length_mm']:g}mm"
    if "thread" in dims:
        return dims["thread"]
    if all(k in dims for k in ("length_mm", "width_mm", "height_mm")):
        return f"{dims['length_mm']:g}x{dims['width_mm']:g}x{dims['height_mm']:g}mm"
    if "length_mm" in dims and "width_mm" in dims:
        return f"{dims['length_mm']:g}x{dims['width_mm']:g}mm"
    if "diameter_mm" in dims and "length_mm" in dims:
        return f"{dims['diameter_mm']:g}mm diameter x {dims['length_mm']:g}mm length"
    if "diameter_mm" in dims:
        return f"{dims['diameter_mm']:g}mm diameter"
    if "length_mm" in dims:
        return f"{dims['length_mm']:g}mm"
    return ""


def _print_settings_to_string(settings: dict | None) -> str:
    if not isinstance(settings, dict):
        return ""
    if settings.get("raw"):
        return str(settings["raw"])
    parts: list[str] = []
    if "layer_mm" in settings:
        parts.append(f"{settings['layer_mm']:g}mm layer height")
    if "infill_pct" in settings:
        parts.append(f"{settings['infill_pct']}% infill")
    if "perimeters" in settings:
        parts.append(f"{settings['perimeters']} perimeters")
    if "nozzle_mm" in settings:
        parts.append(f"{settings['nozzle_mm']:g}mm nozzle")
    return ", ".join(parts)


def _build_sourcing_index(rec: dict) -> dict[str, dict]:
    """component_id → sourcing item dict for fast lookup."""
    out: dict[str, dict] = {}
    for item in rec.get("sourcing", {}).get("items", []):
        cid = item.get("component_id")
        if cid:
            out[cid] = item
    return out


def _is_electrical_pair(src_cat: str, tgt_cat: str) -> bool:
    return src_cat == "electrical" and tgt_cat == "electrical"


# --- per-file writers ------------------------------------------------------

def to_config_json(rec: dict) -> dict:
    """Produce the source-format CONFIG.json content as a dict."""
    sourcing_idx = _build_sourcing_index(rec)
    settings_idx = rec.get("fabrication", {}).get("component_settings", {})

    nodes: list[dict] = []
    cat_by_id: dict[str, str] = {}
    for c in rec["components"]:
        cid = c["component_id"]
        cat_by_id[cid] = c["category"]
        src = sourcing_idx.get(cid, {})
        dim_str = _dims_to_string(c.get("dimensions"))
        node: dict[str, Any] = {
            "id": cid,
            "name": c["display_name"],
            "type": c["type"],
            "category": c["category"],
            "quantity": c["quantity"],
            "description": c.get("description", ""),
        }
        if c.get("material") and c["material"] != "unknown":
            node["material"] = c["material"]
        if dim_str:
            node["dimensions"] = dim_str
        if src.get("product_name"):
            node["productName"] = src["product_name"]
        node["estimatedCost"] = src.get("unit_cost_usd", 0)
        if src.get("url"):
            node["purchaseUrl"] = src["url"]
        ps = _print_settings_to_string(settings_idx.get(cid))
        if ps:
            node["printSettings"] = ps
        nodes.append(node)

    electrical: list[dict] = []
    mechanical: list[dict] = []
    for r in rec.get("relationships", []):
        src_cat = cat_by_id.get(r["source"], "")
        tgt_cat = cat_by_id.get(r["target"], "")
        if r["relation"] == "connects_to" or _is_electrical_pair(src_cat, tgt_cat):
            entry: dict = {
                "source": r["source"],
                "target": r["target"],
            }
            notes = r.get("notes", "")
            # Reconstruct sourcePin/targetPin, protocol, voltage from notes
            entry["type"] = "data" if "protocol" in notes or "pins=" in notes else "power"
            for chunk in notes.split(";"):
                chunk = chunk.strip()
                if chunk.startswith("protocol="):
                    entry["protocol"] = chunk.split("=", 1)[1]
                elif chunk.startswith("voltage="):
                    entry["voltage"] = chunk.split("=", 1)[1]
                elif chunk.startswith("pins="):
                    pin_pair = chunk.split("=", 1)[1]
                    if "->" in pin_pair:
                        sp, tp = pin_pair.split("->", 1)
                        entry["sourcePin"] = sp
                        entry["targetPin"] = tp
                elif chunk.startswith("current="):
                    entry["current"] = chunk.split("=", 1)[1]
                elif chunk and "=" not in chunk and "label" not in entry:
                    entry["label"] = chunk
            electrical.append(entry)
        else:
            mechanical.append({
                "label": r.get("notes") or r["relation"],
                "source": r["source"],
                "target": r["target"],
            })

    # instructionSteps regrouped by phase
    by_phase: dict[str, list[dict]] = {}
    for step in rec.get("instructions", []):
        src_phase = _PHASE_MAP_REVERSE.get(step["phase"], step["phase"])
        by_phase.setdefault(src_phase, []).append({
            "id": step["step_id"],
            "title": step["title"],
            "partIds": step.get("component_ids", []),
        })
    instruction_steps = [{"id": ph, "subSteps": subs} for ph, subs in by_phase.items()]

    out = {
        "plan": rec.get("project", {}).get("summary", ""),
        "nodes": nodes,
        "notes": rec.get("requirements", {}).get("constraints", []),
        "projectName": rec["project"]["name"],
        "originalPrompt": rec["project"]["original_prompt"],
        "instructionSteps": instruction_steps,
        "projectDescription": rec["project"].get("summary", ""),
        "instructionPreamble": {
            "tools": rec.get("requirements", {}).get("tools", []),
            "assumptions": rec.get("requirements", {}).get("assumptions", []),
        },
        "electricalConnections": electrical,
        "mechanicalConnections": mechanical,
        "projectId": rec["project"]["project_id"],
        "visualRef": rec["project"].get("visual_ref"),
    }
    return out


def to_parts_csv(rec: dict) -> str:
    sourcing_idx = _build_sourcing_index(rec)
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")
    writer.writerow(["Name", "Product Name", "Description", "Category", "Type",
                     "Quantity", "Estimated Cost", "Total Cost", "URL"])
    for c in rec["components"]:
        cid = c["component_id"]
        src = sourcing_idx.get(cid, {})
        writer.writerow([
            c["display_name"],
            src.get("product_name", ""),
            c.get("description", ""),
            c["category"],
            c["type"],
            int(c["quantity"]),
            f'{src.get("unit_cost_usd", 0):.2f}',
            f'{src.get("total_cost_usd", 0):.2f}',
            src.get("url") or "",
        ])
    return buf.getvalue()


def to_guide_md(rec: dict) -> str:
    req = rec.get("requirements", {})
    tools = req.get("tools", []) or []
    assumptions = req.get("assumptions", []) or []

    lines: list[str] = []
    lines.append("## Tools")
    for t in tools:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("## Assumptions")
    for a in assumptions:
        lines.append(f"- {a}")
    lines.append("")

    # Group instructions by phase in canonical order
    canonical_phase_order = ["fabrication", "wiring", "bring_up", "assembly", "testing"]
    phase_titles = {
        "fabrication": "Fabrication",
        "wiring": "Wiring",
        "bring_up": "Bring-up",
        "assembly": "Assembly",
        "testing": "Testing",
    }
    by_phase: dict[str, list[dict]] = {}
    for step in rec.get("instructions", []):
        by_phase.setdefault(step["phase"], []).append(step)

    section_num = 0
    for phase in canonical_phase_order:
        steps = by_phase.get(phase)
        if not steps:
            continue
        section_num += 1
        lines.append(f"## {section_num}. {phase_titles[phase]}")
        for i, step in enumerate(steps, start=1):
            lines.append(f"### {section_num}.{i} {step.get('title', '')}")
            er = step.get("expected_result", "")
            if er and er != "unknown":
                lines.append(f"*Expected result:* {er}")
            else:
                lines.append("*(not yet generated)*")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# --- top-level bundle ------------------------------------------------------

def denormalize(rec: dict) -> dict[str, str]:
    """Return a dict of {filename_suffix: file_content} for the 5 files.

    Caller writes them to a `<project_id>_files/` folder.
    """
    config_data = to_config_json(rec)
    return {
        "_CONFIG.json": json.dumps(config_data, indent=2, ensure_ascii=False),
        "_GUIDE.md": to_guide_md(rec),
        "_MECHANICAL_CONNECTIONS.json": json.dumps(
            config_data["mechanicalConnections"], indent=2, ensure_ascii=False
        ),
        "_ELECTRICAL_CONNECTIONS.json": json.dumps(
            config_data["electricalConnections"], indent=2, ensure_ascii=False
        ),
        "_PARTS.csv": to_parts_csv(rec),
    }
