"""Offline (no-LLM) normalizer: raw corpus CONFIG → canonical schema.

=============================== PLAIN-LANGUAGE OVERVIEW =====================
This file is "Stage 1" of the pipeline. Its job is to take ONE messy, raw
project file (a hand-authored `*_CONFIG.json` from the Data/ folder) and turn
it into ONE clean, predictable record that always has the same shape — the
"canonical schema" described in CLAUDE.md.

Think of it like a customs officer for data: every project that comes in gets
its fields renamed, re-ordered, and re-typed into a single standard format so
that everything downstream (the validator, the training-row builder, etc.) can
rely on the same structure every time.

The key rule of this file: it NEVER invents or guesses information. Every
transformation here is "deterministic" — given the same input it always
produces the exact same output, with no AI/LLM involved. When the raw data is
broken or ambiguous (a part that points at a missing component, a dimension
string it can't read), it does NOT make something up; it records a note in the
record's `validation.issues[]` list and moves on.

What it actually does, step by step:
  - parse dimension strings ("400x40x15mm") into numeric fields
  - map each part's raw `type` to a fixed vocabulary of allowed types
  - map free-text connection labels ("servo horn") to fixed relation names
  - flatten the nested instruction phases into one ordered list of steps
  - move 3D-print settings into a `fabrication` section
  - move cost / product-name / purchase-URL info into a `sourcing` section
  - build a `validation` block summarizing how clean the result is

How to read the rest of this file:
  The top half is a toolbox of small, single-purpose helper functions (parse a
  dimension, clean a URL, guess a part's role from its name). The bottom half
  (`normalize_seed` and the `_normalize_*` helpers it calls) is the assembly
  line that uses those tools to build the final record section by section.
============================================================================
"""
from __future__ import annotations
# `re` is Python's regular-expression module. A "regular expression" (regex) is
# a mini-language for describing text patterns — e.g. "a number, then 'mm'".
# This file leans on regex heavily to read the free-form strings in the corpus.
import re
# `Any` is a type hint meaning "a value of any type". It's used below purely as
# documentation for humans/tools; it has no effect when the code runs.
from typing import Any

# --- dimension parsing -----------------------------------------------------
# GOAL of this section: turn human-written size strings into numbers.
# The corpus stores sizes as free text like "400x40x15mm" or "M3x12mm". A model
# can't reliably do math on text, so we pre-compile a set of regex "patterns",
# each one shaped to recognize a different style of size string. `re.compile`
# builds the pattern object once here (faster than rebuilding it on every call).

# Matches a parenthetical aside like " (cable+element)" so we can delete it.
_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*")
# Matches one-or-more underscores in a row (used to turn "_" separators back
# into spaces).
_UNDERSCORE_SEP_RE = re.compile(r"_+")

# Each pattern below targets one common way of writing a size. The `(\d+...)`
# groups are the numbers we want to capture. `[x×]` matches either a normal "x"
# or the multiplication sign "×". `re.IGNORECASE` makes "MM" match "mm".
# A 3-number box: "400x40x15mm" → length × width × height.
_DIM_BOX_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*mm\s*$",
    re.IGNORECASE,
)
_DIM_2D_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*mm\s*$",
    re.IGNORECASE,
)
_DIM_THREAD_LEN_RE = re.compile(
    r"^\s*M(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*mm\s*$",
    re.IGNORECASE,
)
_DIM_THREAD_RE = re.compile(r"^\s*M(\d+(?:\.\d+)?)\s*$", re.IGNORECASE)
_DIM_DIAMETER_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*mm\s+(?:diameter|dia)\s*$", re.IGNORECASE,
)
# Cylinder: "5mm diameter x 80mm length" / "5mm dia x 80mm L"
_DIM_CYLINDER_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*mm\s*(?:dia(?:meter)?|d)\s*[x×]\s*"
    r"(\d+(?:\.\d+)?)\s*mm\s*(?:length|l|long|h|height)?\s*$",
    re.IGNORECASE,
)
# Cylinder reversed: "300mm length, 1.5mm diameter" / "80mm long x 5mm dia"
_DIM_CYLINDER_REV_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*mm\s*(?:length|long|l|h|height)\s*[,x×]?\s*"
    r"(\d+(?:\.\d+)?)\s*mm\s*(?:dia(?:meter)?|d)\s*$",
    re.IGNORECASE,
)
# Tubing: "6mm ID x 9mm OD x 5m L"
_DIM_TUBE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*mm\s*ID\s*[x×]\s*"
    r"(\d+(?:\.\d+)?)\s*mm\s*OD\s*[x×]\s*"
    r"(\d+(?:\.\d+)?)\s*(mm|m)\s*L?\s*$",
    re.IGNORECASE,
)
# Length only: "~0.8m length" / "500mm length"
_DIM_LEN_ONLY_RE = re.compile(
    r"^\s*~?\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)\s*(?:length|long|l)?\s*$",
    re.IGNORECASE,
)


def _to_mm(value: float, unit: str) -> float:
    """Convert a length to millimetres, the canonical unit used everywhere.

    `unit` is the raw unit string we found ("m", "cm", or "mm"). We standardize
    on millimetres so all sizes are directly comparable. `.lower()` makes the
    check case-insensitive ("M" and "m" both mean metres).
    """
    if unit.lower() == "m":
        return value * 1000.0   # 1 metre = 1000 mm
    if unit.lower() == "cm":
        return value * 10.0     # 1 centimetre = 10 mm
    return value                # already mm — leave as-is


def parse_dimensions(raw: str | None) -> dict[str, Any]:
    """Turn a size string into a dict of numbers, e.g. "400x40x15mm" →
    {"length_mm": 400, "width_mm": 40, "height_mm": 15}.

    `raw: str | None` means the input is either a string or `None` (missing).
    We always keep the original text under the "raw" key so nothing is lost,
    then try each known pattern in turn. The first pattern that matches wins and
    we return immediately. If none match, we tag the result `unparsed` so the
    validator knows we couldn't read it (rather than pretending we did).
    """
    # Start the result with the original text preserved.
    out: dict[str, Any] = {"raw": raw}
    # `if not raw` is True for None or an empty string — nothing to parse.
    if not raw:
        return out
    s = raw.strip()  # `.strip()` removes leading/trailing whitespace.
    # Strip parenthetical hints like "(cable+element)" before parsing.
    # `.sub("", s)` replaces every match of the pattern with "" (i.e. deletes it).
    s = _PAREN_RE.sub("", s).strip()
    # Collapse underscore-separators "110mm_Dia_x_30mm_H" → "110mm Dia x 30mm H"
    if "_" in s:
        s = _UNDERSCORE_SEP_RE.sub(" ", s)

    # `pattern.match(s)` returns a "match object" if the pattern fits, else None.
    # `m.group(1)` is the text captured by the first (...) group in the pattern.
    m = _DIM_BOX_RE.match(s)
    if m:
        out["length_mm"] = float(m.group(1))
        out["width_mm"] = float(m.group(2))
        out["height_mm"] = float(m.group(3))
        return out

    m = _DIM_2D_RE.match(s)
    if m:
        out["length_mm"] = float(m.group(1))
        out["width_mm"] = float(m.group(2))
        return out

    m = _DIM_THREAD_LEN_RE.match(s)
    if m:
        out["thread"] = f"M{m.group(1)}"
        out["length_mm"] = float(m.group(2))
        return out

    m = _DIM_THREAD_RE.match(s)
    if m:
        out["thread"] = f"M{m.group(1)}"
        return out

    m = _DIM_DIAMETER_RE.match(s)
    if m:
        out["diameter_mm"] = float(m.group(1))
        return out

    m = _DIM_TUBE_RE.match(s)
    if m:
        out["id_mm"] = float(m.group(1))
        out["od_mm"] = float(m.group(2))
        out["length_mm"] = _to_mm(float(m.group(3)), m.group(4))
        return out

    m = _DIM_CYLINDER_RE.match(s)
    if m:
        out["diameter_mm"] = float(m.group(1))
        out["length_mm"] = float(m.group(2))
        return out

    m = _DIM_CYLINDER_REV_RE.match(s)
    if m:
        out["length_mm"] = float(m.group(1))
        out["diameter_mm"] = float(m.group(2))
        return out

    m = _DIM_LEN_ONLY_RE.match(s)
    if m:
        out["length_mm"] = _to_mm(float(m.group(1)), m.group(2))
        return out

    out["unparsed"] = True
    return out


# --- type/category mapping -------------------------------------------------
# GOAL: collapse the corpus's many free-form part "types" down to the short,
# fixed list the schema allows (see validate.py COMPONENT_TYPES). `_TYPE_MAP`
# is a dictionary — a lookup table from "raw word we might see" → "canonical
# type we want". E.g. both "sensor" and "mcu" become the single type
# "electronic".

_TYPE_MAP = {
    "3d_printed": "3d_printed",
    "misc": "misc",
    "actuator": "electronic",
    "mechanism": "mechanical",
    "module": "electronic",
    "power": "electronic",
    "structural": "mechanical",
    "sensor": "electronic",
    "mcu": "electronic",
    "display": "electronic",
    "enclosure": "mechanical",
    "other": "misc",
}

# If a part's NAME contains any of these words, we treat it as a fastener even
# when its declared type was vague. A tuple (round brackets) is an ordered,
# unchangeable list — fine here because these hints never change at runtime.
_FASTENER_HINTS = ("screw", "nut", "bolt", "washer", "standoff", "spacer", "rivet")


def map_type(raw_type: str | None, name: str, has_print_settings: bool) -> str:
    """Decide a component's canonical `type` from three clues, in priority order.

    1. The raw type word (looked up in _TYPE_MAP).
    2. If that came back "misc", peek at the part's name for fastener words.
    3. If the part has 3D-print settings, it must be 3d_printed regardless.
    """
    # `.get(key, default)` looks up `key` in the dict, returning `default`
    # ("misc") if the key isn't present. `(raw_type or "")` guards against
    # raw_type being None — `None or ""` evaluates to "".
    spec_type = _TYPE_MAP.get((raw_type or "").lower(), "misc")
    if spec_type == "misc":
        low = name.lower()
        # `any(... for h in ...)` is True if AT LEAST ONE hint word appears in
        # the name. This is a "generator expression" feeding the any() function.
        if any(h in low for h in _FASTENER_HINTS):
            return "fastener"
    # Anything with print settings is physically a 3D print, so force that type.
    if has_print_settings and spec_type != "3d_printed":
        return "3d_printed"
    return spec_type


def map_category(raw_category: str | None, spec_type: str) -> str:
    """Decide a component's `category` (electrical vs mechanical).

    Trust the raw category if it's already one of the two we allow; otherwise
    infer it from the type we just computed (electronics → electrical).
    """
    if raw_category in ("electrical", "mechanical"):
        return raw_category
    if spec_type in ("electronic",):
        return "electrical"
    return "mechanical"


# --- relation mapping ------------------------------------------------------
# GOAL: the corpus describes how two parts connect using free text ("servo
# horn", "press-fit into frame"). The schema only allows a fixed set of
# relation names. This section maps the free text onto those names by testing
# a list of regex patterns in order and taking the FIRST one that matches.

# Order matters: more-specific physical mechanisms first; generic fallbacks last.
# Each entry is a (pattern, relation_name) pair. `re.I` is shorthand for
# re.IGNORECASE. The `|` inside a pattern means "or" — any listed word matches.
_RELATION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"servo[_ ]?horn|rotational[_ ]joint|pivot|axle|bearing|rotate|shaft\b", re.I), "rotates_on"),
    (re.compile(r"wrap(?:ped)?[_ ]around|pulley|belt[_ ]around|cable[_ ]around|routed|guide[_ ]for", re.I), "routed_around"),
    (re.compile(r"hous(?:ed|ing)|enclos|contain|hold[s]?[_ ]in[_ ]place|integrate|placed[_ ]inside", re.I), "contains"),
    (re.compile(
        r"barb|hose[_ ]clamp|press[_ ]?fit|thread|screw[_ ]into|fasten[_ ]into|t[-_ ]nut|"
        # Fastener-spec labels: anywhere there's an M-size and a fastener word.
        r"\bM\d.{0,40}\b(?:screws?|bolts?|nuts?|hardware)\b",
        re.I,
    ), "fastens_into"),
    (re.compile(r"connect|wire|cable|signal|harness", re.I), "connects_to"),
    (re.compile(r"support|backed[_ ]by|rests[_ ]on|sits[_ ]on", re.I), "supported_by"),
    (re.compile(r"position|locate|align", re.I), "positions"),
    # Fastener-source rows: "M3 bolts", "M2x6mm screws", "M3 nuts"
    (re.compile(r"^secur|^screws?\b|^bolts?\b|^nuts?\b|fastened|secures", re.I), "secured_by"),
    (re.compile(r"mount", re.I), "mounted_on"),
    (re.compile(r"attach|fit|snap|clip|glue|adhesive", re.I), "attached_to"),
]


def map_relation(raw_label: str | None) -> str:
    """Return the canonical relation name for a free-text connection label.

    Walks the pattern list top-to-bottom; the first pattern that appears
    anywhere in the label wins. If the label is empty or nothing matches, we
    fall back to the safest generic relation, "attached_to".
    """
    if not raw_label:
        return "attached_to"
    # Unpack each (pattern, relation) pair as we loop. `.search` looks for the
    # pattern ANYWHERE in the string (unlike `.match`, which only checks the start).
    for pat, rel in _RELATION_PATTERNS:
        if pat.search(raw_label):
            return rel
    return "attached_to"


# --- print settings parser -------------------------------------------------
# GOAL: pull individual 3D-printer settings out of a free-text blurb like
# "20% infill, 0.2mm layer, 3 perimeters, PETG". Unlike dimension parsing,
# here we collect EVERY setting we can find (they're independent), so we use
# `.search` once per setting rather than trying whole-string patterns.

_INFILL_RE = re.compile(r"(\d+)\s*%\s*infill", re.I)
_LAYER_RE = re.compile(r"(\d+(?:\.\d+)?)\s*mm\s*layer", re.I)
_PERIMETER_RE = re.compile(r"(\d+)\s*perimeter", re.I)
_NOZZLE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*mm\s*nozzle", re.I)
_MATERIAL_HINT_RE = re.compile(r"\b(PLA|PETG|ABS|ASA|TPU|Nylon|PC)\b", re.I)


def parse_print_settings(raw: str | None) -> dict[str, Any]:
    """Extract structured print settings from a free-text settings string.

    `if m := PATTERN.search(raw)` is the "walrus operator": it both assigns the
    match to `m` AND checks whether it's truthy, in one line. So each block
    reads "if this setting is present, capture its number into `out`".
    """
    out: dict[str, Any] = {"raw": raw}
    if not raw:
        return out
    if m := _INFILL_RE.search(raw):
        out["infill_pct"] = int(m.group(1))
    if m := _LAYER_RE.search(raw):
        out["layer_mm"] = float(m.group(1))
    if m := _PERIMETER_RE.search(raw):
        out["perimeters"] = int(m.group(1))
    if m := _NOZZLE_RE.search(raw):
        out["nozzle_mm"] = float(m.group(1))
    if m := _MATERIAL_HINT_RE.search(raw):
        out["material_hint"] = m.group(1).upper()
    return out


# --- id normalization ------------------------------------------------------
# GOAL: every id in the dataset must be "snake_case" — lowercase letters,
# digits, and underscores only (e.g. "servo_horn_left"). This guarantees ids
# are safe to use as filenames, JSON keys, and references everywhere.

# Matches any run of characters that AREN'T allowed in an id. The `^` inside
# `[...]` means "not", so this is "one-or-more disallowed characters".
_BAD_ID_CHARS = re.compile(r"[^a-z0-9_]+")


def to_snake_id(s: str) -> str:
    """Convert arbitrary text into a clean snake_case id.

    Example: "Servo Horn (left)" → "servo_horn_left". The steps are chained:
    lowercase it, turn spaces/dashes into underscores, delete anything still
    illegal, collapse repeated underscores, and trim stray edge underscores.
    `return s or "unknown"` guards the rare case where everything got stripped
    away (an all-symbols name) so we never return an empty id.
    """
    s = s.strip().lower().replace("-", "_").replace(" ", "_")
    s = _BAD_ID_CHARS.sub("_", s)        # delete any leftover illegal chars
    s = re.sub(r"_+", "_", s).strip("_")  # "__" → "_", then trim edge "_"
    return s or "unknown"


# --- functional role inference --------------------------------------------
# GOAL: guess WHAT A PART DOES in the project (its "functional role") from its
# name. "esp32" → main_controller, "18650" → power_source, and so on. Same
# first-match-wins pattern-list technique as relation mapping above.

_ROLE_HINTS = [
    (re.compile(r"mcu|controller|esp32|raspberry|stm32|arduino|teensy", re.I), "main_controller"),
    (re.compile(r"battery|lipo|li[-_ ]?ion|18650", re.I), "power_source"),
    (re.compile(r"regulator|buck|boost|converter|psu", re.I), "power_conditioning"),
    (re.compile(r"charger|tp4056|bms", re.I), "charging"),
    (re.compile(r"display|screen|lcd|oled|matrix", re.I), "display"),
    (re.compile(r"button|switch|encoder|keypad|input", re.I), "user_input"),
    (re.compile(r"sensor|imu|gyro|accelerometer|bme|tof|lidar", re.I), "sensing"),
    (re.compile(r"motor|servo|actuator|solenoid", re.I), "actuation"),
    (re.compile(r"speaker|buzzer|piezo|amp", re.I), "audio_output"),
    (re.compile(r"antenna|rf|radio|lora|wifi|bluetooth", re.I), "wireless"),
    (re.compile(r"mount|bracket|holder|standoff", re.I), "mounting"),
    (re.compile(r"enclosure|case|housing|cover|panel|body", re.I), "enclosure"),
    (re.compile(r"screw|nut|bolt|washer", re.I), "fastener"),
    (re.compile(r"frame|chassis|rail|beam|spar", re.I), "structural"),
    (re.compile(r"bearing|axle|shaft|coupler", re.I), "kinematic"),
]


def infer_functional_role(name: str, raw_type: str | None) -> str:
    """Best-effort guess of a component's role from its name.

    Falls back to the raw type word if no name pattern matches, and finally to
    "unknown" — we'd rather honestly say "unknown" than invent a role.
    """
    for pat, role in _ROLE_HINTS:
        if pat.search(name):
            return role
    if raw_type:
        return raw_type
    return "unknown"


# --- skill level inference -------------------------------------------------
# GOAL: label the whole project beginner / intermediate / advanced by scanning
# its assumptions and notes for tell-tale phrases.

_BEGINNER_HINTS = ("basic", "no prior", "first project")
_ADVANCED_HINTS = ("advanced", "rf design", "high voltage", "professional", "fpga", "rtos")


def infer_skill_level(assumptions: list[str], notes: list[str]) -> str:
    """Classify difficulty from free-text hints. Advanced wins over beginner.

    `" ".join(a + b)` glues the two lists of strings into one big string with
    spaces between, so we can search all the text at once. Default is the
    middle ground, "intermediate".
    """
    text = " ".join(assumptions + notes).lower()
    if any(h in text for h in _ADVANCED_HINTS):
        return "advanced"
    if any(h in text for h in _BEGINNER_HINTS):
        return "beginner"
    return "intermediate"


# --- url filtering ---------------------------------------------------------

def clean_url(url: str | None) -> str | None:
    """Keep a purchase URL only if it looks real; otherwise return None.

    Per CLAUDE.md we must never teach the model to hallucinate links, so we drop
    anything that isn't a proper http(s) address or that looks truncated
    ("...") or like a placeholder ("N/A"). Returning None means "no link".
    """
    if not url:
        return None
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return None
    if "N/A" in url or url.endswith("..."):
        return None
    return url


# --- top-level normalizer --------------------------------------------------
# Everything above was the toolbox. Everything below is the ASSEMBLY LINE that
# uses those tools. `normalize_seed` (at the very bottom) is the public entry
# point; it calls one `_normalize_<section>` helper per schema section, threading
# a shared `issues` list through them all so every problem is collected in one
# place. (A leading underscore on a name is a Python convention meaning
# "internal helper — not part of this module's public interface".)

# Maps the corpus's short phase words to the schema's phase names.
_PHASE_MAP = {
    "fabricate": "fabrication",
    "wire": "wiring",
    "bringup": "bring_up",
    "assemble": "assembly",
    "test": "testing",
}


def _normalize_components(
    raw_nodes: list[dict], issues: list[dict]
) -> tuple[list[dict], dict[str, str]]:
    """Turn the raw `nodes` list into clean component records.

    Returns TWO things (a "tuple"): the list of cleaned components, AND an
    `id_map` translating each part's original id → its new snake_case id. The
    later helpers need that map to rewrite references (a relationship that
    pointed at the old id must now point at the new one).

    `issues` is passed in and appended to in place — that's how problems found
    here (duplicate ids, bad quantities) bubble up to the final validation block.
    """
    components: list[dict] = []
    id_map: dict[str, str] = {}
    seen_ids: set[str] = set()  # a `set` tracks which ids we've used (fast lookup)

    # Defensive guard: if the corpus gave us something other than a list, treat
    # it as empty rather than crashing. `isinstance(x, list)` asks "is x a list?"
    if not isinstance(raw_nodes, list):
        raw_nodes = []
    for node in raw_nodes:
        if not isinstance(node, dict):
            continue  # `continue` skips to the next loop item, ignoring junk
        # Use the node's id if it has one, else derive an id from its name.
        raw_id = node.get("id") or to_snake_id(node.get("name", "unknown"))
        spec_id = to_snake_id(raw_id)
        # If two parts would end up with the same id, keep the first and append
        # "_2", "_3", … to the rest so every id stays unique. We log a warning.
        if spec_id in seen_ids:
            issues.append({
                "severity": "warn",
                "code": "duplicate_id",
                "message": f"duplicate component id {spec_id!r}, suffixing",
                "refs": [spec_id],
            })
            i = 2
            while f"{spec_id}_{i}" in seen_ids:  # find the first free suffix
                i += 1
            spec_id = f"{spec_id}_{i}"
        seen_ids.add(spec_id)
        id_map[raw_id] = spec_id  # remember old → new so refs can be rewritten

        name = node.get("name") or raw_id
        raw_type = node.get("type")
        has_print = "printSettings" in node  # True if this part has print info
        spec_type = map_type(raw_type, name, has_print)
        category = map_category(node.get("category"), spec_type)
        # Fasteners default to "steel"; everything else defaults to "unknown"
        # (we never guess a material we don't actually know).
        material = node.get("material") or ("unknown" if spec_type != "fastener" else "steel")

        # Quantities must be whole numbers. `try/except` runs the risky
        # conversion and, if it throws an error (text like "a few"), falls back
        # to 1 and records a warning instead of crashing the whole run.
        try:
            quantity = int(node.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1
            issues.append({
                "severity": "warn", "code": "invalid_quantity",
                "message": f"component {spec_id} quantity coerced to 1",
                "refs": [spec_id],
            })

        # Build the final, schema-shaped component record. Note `fabrication_ref`
        # is the part's own id only if it has print settings, else None — this is
        # the link the fabrication section uses to find its settings later.
        components.append({
            "component_id": spec_id,
            "display_name": name,
            "category": category,
            "type": spec_type,
            "material": material,
            "quantity": quantity,
            "description": node.get("description", ""),
            "dimensions": parse_dimensions(node.get("dimensions")),
            "functional_role": infer_functional_role(name, raw_type),
            "fabrication_ref": spec_id if has_print else None,
            "sourcing_ref": spec_id,
        })

    return components, id_map


def _normalize_relationships(
    raw_cfg: dict, id_map: dict[str, str], issues: list[dict]
) -> list[dict]:
    """Build the relationship graph from the raw electrical + mechanical links.

    The corpus stores connections in two separate lists. We translate both into
    the same uniform relationship shape (source, relation, target, …). Crucially,
    we look every endpoint up in `id_map`: if a connection points at a part id
    that doesn't exist, that's a "dangling reference" — we record an ERROR and
    DROP the bad relationship rather than emitting a broken graph.
    """
    rels: list[dict] = []

    # `.get("electricalConnections", []) or []` returns the list if present, or
    # an empty list if the key is missing OR explicitly set to null/empty.
    for c in raw_cfg.get("electricalConnections", []) or []:
        if not isinstance(c, dict):
            continue
        # Translate the raw endpoint ids to our new ids. `.get` returns None if
        # the id isn't in the map (i.e. the referenced part doesn't exist).
        src = id_map.get(c.get("source"))
        tgt = id_map.get(c.get("target"))
        if not src or not tgt:
            issues.append({
                "severity": "error", "code": "dangling_ref",
                "message": f"electrical conn {c.get('source')!r}->{c.get('target')!r} "
                           f"references missing component",
                "refs": [c.get("source"), c.get("target")],
            })
            continue
        # Gather any extra electrical detail (protocol, voltage, pin pairing)
        # into a human-readable notes string. Each `(x := ...)` walrus both
        # fetches the value and checks it's present before adding it.
        notes = []
        if (p := c.get("protocol")): notes.append(f"protocol={p}")
        if (v := c.get("voltage")): notes.append(f"voltage={v}")
        if (sp := c.get("sourcePin")) and (tp := c.get("targetPin")):
            notes.append(f"pins={sp}->{tp}")
        # Electrical links are always the "connects_to" relation.
        rels.append({
            "source": src,
            "relation": "connects_to",
            "target": tgt,
            "required": True,
            # Join the notes with "; ", or fall back to the raw label if none.
            "notes": "; ".join(notes) or c.get("label", ""),
        })

    for c in raw_cfg.get("mechanicalConnections", []) or []:
        if not isinstance(c, dict):
            continue
        src = id_map.get(c.get("source"))
        tgt = id_map.get(c.get("target"))
        if not src or not tgt:
            issues.append({
                "severity": "error", "code": "dangling_ref",
                "message": f"mechanical conn {c.get('source')!r}->{c.get('target')!r} "
                           f"references missing component",
                "refs": [c.get("source"), c.get("target")],
            })
            continue
        # Mechanical links use map_relation() to choose the relation from the
        # free-text label ("press-fit", "screws into", …).
        rels.append({
            "source": src,
            "relation": map_relation(c.get("label")),
            "target": tgt,
            "required": True,
            "notes": c.get("label") or "",
        })

    return rels


def _normalize_instructions(
    raw_steps, id_map: dict[str, str], issues: list[dict]
) -> list[dict]:
    """Flatten the nested phase→subStep tree into ONE ordered list of steps.

    The corpus groups steps under phases ("fabricate", "assemble"). The schema
    wants a single flat list where each step carries its own `phase` field and
    points back (`dependencies`) at the step before it, giving a simple linear
    build order. We also rewrite each step's part references through id_map and
    flag any that point at a missing part.
    """
    out: list[dict] = []
    last_step_id: str | None = None  # remembers the previous step for chaining
    if not isinstance(raw_steps, list):
        return out
    for phase in raw_steps:
        # Tolerate models that emit a flat list of strings, or phase entries
        # missing subSteps. Coerce into the expected shape rather than crash.
        if isinstance(phase, str):
            phase_id = _PHASE_MAP.get(phase, "unknown")
            sub_steps = [{"title": phase}]
        elif isinstance(phase, dict):
            phase_id = _PHASE_MAP.get(phase.get("id"), phase.get("id", "unknown"))
            sub_steps = phase.get("subSteps", [])
            if not isinstance(sub_steps, list):
                sub_steps = []
        else:
            continue
        for sub in sub_steps:
            if isinstance(sub, str):
                sub = {"title": sub}  # a bare string becomes a titled step
            elif not isinstance(sub, dict):
                continue
            # Use the step's own id if given, else auto-name it "<phase>_<N>".
            # `len(out)+1` is the 1-based count of steps emitted so far.
            step_id = to_snake_id(sub.get("id") or f"{phase_id}_{len(out)+1}")
            comp_ids: list[str] = []
            part_ids = sub.get("partIds", [])
            if not isinstance(part_ids, list):
                part_ids = []
            # Rewrite each referenced part id through id_map. A reference to a
            # part that doesn't exist is a dangling step ref — flagged as ERROR.
            for pid in part_ids:
                if not isinstance(pid, str):
                    continue
                mapped = id_map.get(pid)
                if mapped:
                    comp_ids.append(mapped)
                else:
                    issues.append({
                        "severity": "error", "code": "dangling_step_ref",
                        "message": f"instruction step {step_id!r} references missing part {pid!r}",
                        "refs": [pid],
                    })
            out.append({
                "step_id": step_id,
                "phase": phase_id if isinstance(phase_id, str) else "unknown",
                "title": sub.get("title", ""),
                "component_ids": comp_ids,
                # Each step depends on the one before it → a simple linear order.
                "dependencies": [last_step_id] if last_step_id else [],
                "expected_result": "unknown",
            })
            last_step_id = step_id  # this step becomes the next step's dependency
    return out


def _normalize_fabrication(raw_nodes: list[dict], id_map: dict[str, str]) -> dict:
    """Collect manufacturing info into the `fabrication` section.

    Two outputs: `component_settings` maps each 3D-printed part's id → its parsed
    print settings, and `processes` is the SET of distinct manufacturing methods
    used (3D printing, machining, laser cutting). A `set` automatically de-dupes,
    so each process is listed once no matter how many parts use it.
    """
    component_settings: dict[str, dict] = {}
    processes_seen: set[str] = set()
    for node in raw_nodes or []:
        if not isinstance(node, dict):
            continue
        if "printSettings" in node:
            raw_id = node.get("id")
            spec_id = id_map.get(raw_id, to_snake_id(raw_id or ""))
            component_settings[spec_id] = parse_print_settings(node["printSettings"])
            processes_seen.add("fdm_3d_printing")
        elif node.get("type") == "machined":
            processes_seen.add("machining")
        elif node.get("type") == "laser_cut":
            processes_seen.add("laser_cutting")
    return {
        "processes": sorted(processes_seen),  # sorted() → stable, ordered output
        "component_settings": component_settings,
        "post_processing": [],
        "tolerances": {},
    }


def _normalize_sourcing(raw_nodes: list[dict], id_map: dict[str, str]) -> dict:
    """Build the `sourcing` (purchasing) section and tally up costs.

    For each part we emit a line item with unit cost, quantity, and line total
    (unit × qty), keep only a cleaned purchase URL, and accumulate a grand total.
    `total` and `priced` are running tallies updated as we loop.
    """
    items: list[dict] = []
    total = 0.0
    priced = 0  # how many parts actually had a price (> 0)
    for node in raw_nodes or []:
        if not isinstance(node, dict):
            continue
        raw_id = node.get("id")
        spec_id = id_map.get(raw_id, to_snake_id(raw_id or ""))
        # Parse cost and quantity defensively — bad values fall back to 0/1
        # instead of crashing. `float(...)` allows decimals like 2.50.
        try:
            unit = float(node.get("estimatedCost", 0))
        except (TypeError, ValueError):
            unit = 0.0
        try:
            qty = int(node.get("quantity", 1))
        except (TypeError, ValueError):
            qty = 1
        line_total = round(unit * qty, 2)  # round to 2 decimal places (cents)
        url = clean_url(node.get("purchaseUrl"))
        items.append({
            "component_id": spec_id,
            "product_name": node.get("productName") or node.get("name", ""),
            "unit_cost_usd": unit,
            "quantity": qty,
            "total_cost_usd": line_total,
            "vendor": None,
            "url": url,
        })
        if unit > 0:
            priced += 1
        total += line_total
    return {
        "items": items,
        "cost_summary": {
            "total_usd": round(total, 2),
            "components_priced": priced,
            "components_total": len(items),
        },
        "vendors": [],
    }


def _normalize_requirements(raw_cfg: dict) -> dict:
    """Build the `requirements` section (tools, assumptions, skill, constraints).

    `[str(n) for n in ...]` is a "list comprehension": it builds a new list by
    converting every note `n` to a string. We compute skill_level from the text
    and leave safety_notes empty (the corpus doesn't supply them reliably).
    """
    preamble = raw_cfg.get("instructionPreamble") or {}
    tools = preamble.get("tools", [])
    assumptions = preamble.get("assumptions", [])
    notes = [str(n) for n in raw_cfg.get("notes", [])]
    return {
        "tools": tools,
        "assumptions": assumptions,
        "skill_level": infer_skill_level(assumptions, notes),
        "safety_notes": [],
        "constraints": notes,
    }


def _build_validation(issues: list[dict]) -> dict:
    """Summarize the collected issues into the record's `validation` block.

    This converts the raw issue list into pass/fail booleans plus a confidence
    score. The score is a quick heuristic: 1.0 if perfectly clean, 0.7 if only
    warnings, 0.4 if there's at least one error. (Schema validity is asserted
    True here because this normalizer always emits schema-shaped output; the
    separate validate.py double-checks that independently.)
    """
    # `any(... for i in issues)` is True if AT LEAST ONE issue is an "error".
    has_error = any(i["severity"] == "error" for i in issues)
    return {
        "schema_valid": True,
        "reference_integrity_valid": not has_error,  # `not` flips True/False
        "manufacturability_valid": True,
        "naming_consistency_valid": not any(
            i["code"] == "duplicate_id" for i in issues
        ),
        "issues": issues,
        # A chained if/else expression picks the score in one line.
        "confidence_score": (
            1.0 if not issues
            else (0.7 if not has_error else 0.4)
        ),
    }


def normalize_seed(slug: str, raw_cfg: dict) -> dict:
    """Convert one raw corpus CONFIG into the canonical CLAUDE.md schema.

    THIS IS THE PUBLIC ENTRY POINT of the file — the function the rest of the
    pipeline calls. It orchestrates all the `_normalize_*` helpers above and
    stitches their outputs into the final 8-section record. `slug` is the
    project's folder name; `raw_cfg` is the parsed raw CONFIG.json.

    A single shared `issues` list is created here and passed into every helper,
    so by the end it holds every problem found anywhere, ready to summarize.
    """
    issues: list[dict] = []

    # Build each section in order. Components MUST come first because it produces
    # the `id_map` that relationships and instructions need to rewrite refs.
    components, id_map = _normalize_components(raw_cfg.get("nodes", []), issues)
    relationships = _normalize_relationships(raw_cfg, id_map, issues)
    instructions = _normalize_instructions(
        raw_cfg.get("instructionSteps", []), id_map, issues
    )
    # A project with no build steps can't train Mode E (project→instructions),
    # so flag that as an error the auto-repair step (in run.py) can later fix.
    if not instructions:
        issues.append({
            "severity": "error",
            "code": "empty_instructions",
            "message": "no instruction steps in seed; cannot train project→instructions mode",
            "refs": [],
        })
    fabrication = _normalize_fabrication(raw_cfg.get("nodes", []), id_map)
    sourcing = _normalize_sourcing(raw_cfg.get("nodes", []), id_map)
    requirements = _normalize_requirements(raw_cfg)

    # Infer the project's overall category by counting how many parts are
    # electrical vs mechanical. A project with both is "electromechanical".
    cat_counts: dict[str, int] = {}
    for c in components:
        cat_counts[c["category"]] = cat_counts.get(c["category"], 0) + 1
    has_e = cat_counts.get("electrical", 0) > 0
    has_m = cat_counts.get("mechanical", 0) > 0
    project_category = (
        "electromechanical" if has_e and has_m
        else "electronics" if has_e
        else "mechanical" if has_m
        else "unknown"
    )

    project_id = to_snake_id(slug)
    # Assemble the final record: the 8 top-level sections required by the schema.
    # `variant_type` is "seed" because this is an original project (not a
    # generated variant); `seed_project_id` points to itself for the same reason.
    out = {
        "project": {
            "project_id": project_id,
            "name": raw_cfg.get("projectName", slug),
            "category": project_category,
            # Use the description, or the first 300 chars of the plan as backup.
            "summary": raw_cfg.get("projectDescription") or raw_cfg.get("plan", "")[:300],
            "original_prompt": raw_cfg.get("originalPrompt", ""),
            "variant_type": "seed",
            "seed_project_id": project_id,
            "visual_ref": f"{project_id}_VISUAL.png",
        },
        "requirements": requirements,
        "components": components,
        "relationships": relationships,
        "fabrication": fabrication,
        "instructions": instructions,
        "sourcing": sourcing,
        "validation": _build_validation(issues),
    }
    return out
