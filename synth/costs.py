"""Shared sourcing-cost recomputation.

One canonical place to rebuild `rec['sourcing']['cost_summary']` from its
items, so the seed normalizer, the fixup pass, the programmatic variants, and
the gap-patcher all agree on the shape (`total_usd`, `components_priced`,
`components_total`).
"""
from __future__ import annotations


def recompute_cost_summary(rec: dict, *, refresh_item_totals: bool = False) -> None:
    """Rebuild `rec['sourcing']['cost_summary']` in place from its items.

    With `refresh_item_totals=True`, each item's `total_cost_usd` is first
    recomputed as `unit_cost_usd * quantity` — used after a transform changes
    unit costs or quantities (e.g. the programmatic positive variants). When
    callers have already set item totals themselves (fixup, gap-patcher) leave
    it False so the existing per-item totals are trusted as-is.
    """
    total = 0.0
    priced = 0
    for item in rec["sourcing"]["items"]:
        if refresh_item_totals:
            item["total_cost_usd"] = round(item["unit_cost_usd"] * item["quantity"], 2)
        total += item["total_cost_usd"]
        if item["unit_cost_usd"] > 0:
            priced += 1
    rec["sourcing"]["cost_summary"] = {
        "total_usd": round(total, 2),
        "components_priced": priced,
        "components_total": len(rec["components"]),
    }
