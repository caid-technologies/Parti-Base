"""Audit prompt ↔ design alignment.

For each record, extract prompt keywords across known categories and check
whether the design (components, requirements, costs) covers what the prompt
asks for. Flag mismatches as warnings.

This is a quality-signal pass, not strict validation. Outputs a report; does
not modify records. Designed to be re-run after every dataset regeneration.
"""
from __future__ import annotations
import re
from typing import Any

# Keyword → (category, design-side detector function)
# Each detector takes a normalized record and returns True if the prompt's
# claim is supported.

# --- prompt keyword vocabulary --------------------------------------------

KEYWORD_VOCAB: dict[str, list[str]] = {
    "wifi": ["wifi", "wi-fi", "wireless internet"],
    "bluetooth": ["bluetooth", "ble"],
    "lora": ["lora", "lorawan"],
    "esp32": ["esp32"],
    "esp8266": ["esp8266"],
    "raspberry_pi": ["raspberry pi", "rpi", "raspi"],
    "arduino": ["arduino"],
    "stm32": ["stm32"],

    "battery": ["battery", "rechargeable", "lipo", "li-ion", "18650"],
    "usb_c": ["usb-c", "usb c", "type-c"],
    "solar": ["solar", "photovoltaic"],

    "display": ["display", "screen", "oled", "lcd", "led matrix", "e-ink"],
    "camera": ["camera", "image sensor", "webcam"],
    "microphone": ["microphone", "mic"],
    "speaker": ["speaker", "buzzer", "audio out"],

    "temperature_sensor": ["temperature", "temp sensor", "thermometer", "bme280", "dht22"],
    "humidity_sensor": ["humidity", "bme280", "dht22"],
    "motion_sensor": ["motion", "pir", "accelerometer", "imu", "gyro"],
    "distance_sensor": ["distance", "ultrasonic", "lidar", "tof", "tfmini"],

    "motor": ["motor", "servo", "stepper"],
    "pump": ["pump"],
    "fan": ["fan"],

    "rgb_led": ["rgb", "ws2812", "neopixel", "addressable led", "color led"],
    "remote_control": ["remote control", "ir remote", "rf remote", "handheld remote"],

    "compact": ["compact", "small", "tiny", "miniature", "portable"],
    "large": ["large", "big", "full-size"],
    "waterproof": ["waterproof", "ip67", "ip65", "weatherproof"],
}

# Per-keyword: where in the record to look for evidence of coverage.
# Each entry is a tuple of (component_name_patterns, component_role_patterns).

KEYWORD_COVERAGE: dict[str, tuple[list[str], list[str]]] = {
    "wifi": (["esp32", "esp8266", "wifi", "wireless"], ["wireless"]),
    "bluetooth": (["esp32", "bluetooth", "ble", "hm-10"], ["wireless"]),
    "lora": (["lora", "sx127", "rfm9"], ["wireless"]),
    "esp32": (["esp32"], ["main_controller"]),
    "esp8266": (["esp8266", "nodemcu", "wemos"], ["main_controller"]),
    "raspberry_pi": (["raspberry", "pi"], ["main_controller"]),
    "arduino": (["arduino", "uno", "nano", "mega", "atmega"], ["main_controller"]),
    "stm32": (["stm32", "bluepill"], ["main_controller"]),

    "battery": (["battery", "lipo", "li-ion", "18650", "cell"], ["power_source"]),
    "usb_c": (["usb-c", "usb_c", "type-c", "tp4056"], []),
    "solar": (["solar", "photovoltaic", "panel"], ["power_source"]),

    "display": (["display", "screen", "oled", "lcd", "matrix", "e-ink"], ["display"]),
    "camera": (["camera", "cam", "imx", "ov2640"], ["sensing"]),
    "microphone": (["microphone", "mic", "inmp", "max9814"], ["sensing"]),
    "speaker": (["speaker", "buzzer", "piezo"], ["audio_output"]),

    "temperature_sensor": (["bme280", "bmp", "dht", "ds18b20", "temperature"], ["sensing"]),
    "humidity_sensor": (["bme280", "dht", "humidity", "sht"], ["sensing"]),
    "motion_sensor": (["pir", "mpu", "imu", "accelerometer", "gyro", "motion"], ["sensing"]),
    "distance_sensor": (["hc-sr04", "vl53", "lidar", "tfmini", "tof", "distance", "ultrasonic"], ["sensing"]),

    "motor": (["motor", "servo", "stepper", "nema", "dc_motor"], ["actuation"]),
    "pump": (["pump"], ["actuation"]),
    "fan": (["fan", "cooler"], ["actuation"]),

    "rgb_led": (["ws2812", "neopixel", "rgb", "apa102"], ["display"]),
    "remote_control": (["ir_receiver", "rf_receiver", "remote", "vs1838"], ["user_input"]),

    "compact": ([], []),
    "large": ([], []),
    "waterproof": ([], []),
}


def _detect_prompt_keywords(prompt: str) -> list[str]:
    p = prompt.lower()
    hits: list[str] = []
    for key, aliases in KEYWORD_VOCAB.items():
        for alias in aliases:
            # Use word boundary for short aliases to avoid e.g. "esp32" matching inside "esp8266"
            if len(alias) <= 6:
                if re.search(rf"\b{re.escape(alias)}\b", p):
                    hits.append(key)
                    break
            else:
                if alias in p:
                    hits.append(key)
                    break
    return hits


def _has_coverage(rec: dict, keyword: str) -> bool:
    """Check if the design covers the given prompt keyword."""
    name_pats, role_pats = KEYWORD_COVERAGE.get(keyword, ([], []))
    if not name_pats and not role_pats:
        # No detector → assume covered (we don't audit subjective traits like "compact")
        return True

    for c in rec.get("components", []):
        text = " ".join([
            c.get("component_id", ""),
            c.get("display_name", ""),
            c.get("description", ""),
        ]).lower()
        for pat in name_pats:
            if pat in text:
                return True
        role = (c.get("functional_role") or "").lower()
        for pat in role_pats:
            if pat == role:
                return True
    return False


def audit_record(rec: dict) -> dict[str, Any]:
    """Return audit findings for one record."""
    prompt = rec.get("project", {}).get("original_prompt", "") or ""
    pid = rec.get("project", {}).get("project_id", "")
    keywords = _detect_prompt_keywords(prompt)
    mismatches: list[dict] = []
    for kw in keywords:
        if not _has_coverage(rec, kw):
            mismatches.append({
                "keyword": kw,
                "category": kw,
                "message": f"prompt mentions {kw!r} but no component appears to cover it",
            })
    return {
        "project_id": pid,
        "variant_type": rec.get("project", {}).get("variant_type", ""),
        "prompt_keywords": keywords,
        "mismatches": mismatches,
        "coverage_ratio": (
            round(1.0 - len(mismatches) / len(keywords), 3) if keywords else 1.0
        ),
    }


def audit_dataset(records: list[dict]) -> dict[str, Any]:
    """Run audit on every record. Returns full report dict."""
    per_record = [audit_record(r) for r in records]

    total_records = len(per_record)
    with_keywords = sum(1 for r in per_record if r["prompt_keywords"])
    with_mismatches = sum(1 for r in per_record if r["mismatches"])
    total_mismatches = sum(len(r["mismatches"]) for r in per_record)

    # Frequency of each mismatching keyword
    miss_freq: dict[str, int] = {}
    for r in per_record:
        for m in r["mismatches"]:
            miss_freq[m["keyword"]] = miss_freq.get(m["keyword"], 0) + 1

    # By variant_type
    by_type: dict[str, dict[str, int]] = {}
    for r in per_record:
        vt = r["variant_type"] or "unknown"
        d = by_type.setdefault(vt, {"records": 0, "with_mismatches": 0, "mismatches": 0})
        d["records"] += 1
        if r["mismatches"]:
            d["with_mismatches"] += 1
        d["mismatches"] += len(r["mismatches"])

    summary = {
        "total_records": total_records,
        "records_with_prompt_keywords": with_keywords,
        "records_with_mismatches": with_mismatches,
        "total_mismatches": total_mismatches,
        "mismatch_keyword_frequency": dict(
            sorted(miss_freq.items(), key=lambda x: -x[1])
        ),
        "by_variant_type": by_type,
    }
    return {"summary": summary, "per_record": per_record}
