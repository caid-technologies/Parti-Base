"""Gate tests for testcases.py's pure (no-LLM) pieces.

Runnable two ways:
    pytest tests/test_testcases.py
    python tests/test_testcases.py         # no pytest needed
"""
from __future__ import annotations

import base64
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from testcases import (  # noqa: E402
    DEFAULT_TYPES,
    INPUT_TYPES,
    SYSTEM_PROMPT,
    build_cases,
    build_chat_payload,
    find_sketch,
    latin1_safe,
    pdf_text,
    project_slugs,
    render_pdf,
    score_case,
    user_payload,
)

ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "out" / "normalized"

# a tiny but real PNG header + payload; enough for base64/data-uri plumbing
_FAKE_PNG = b"\x89PNG\r\n\x1a\nfakebody"


def _tmpdir() -> Path:
    return Path(tempfile.mkdtemp(prefix="testcases_"))


def _sketch_dir_for(slugs: list[str], ext: str = ".png") -> Path:
    d = _tmpdir()
    for s in slugs:
        (d / f"{s}{ext}").write_bytes(_FAKE_PNG)
    return d


def test_project_slugs_sorted_and_complete():
    slugs = project_slugs()
    assert slugs == sorted(slugs)
    assert "digital_desk_clock" in slugs
    assert len(slugs) >= 42


def test_latin1_safe_replaces_non_latin1():
    # the orbіz project name carries a Cyrillic і — must not crash fpdf2
    out = latin1_safe("orbіz sniper — ok")
    out.encode("latin-1")  # must be encodable now
    assert "orb" in out and "z sniper" in out


def test_pdf_roundtrip_preserves_text():
    tmp = _tmpdir()
    try:
        pdf = tmp / "t.pdf"
        render_pdf("## Tools\n- Soldering iron with fine tip\n\nDone.", pdf)
        text = pdf_text(pdf)
        assert "Soldering iron with fine tip" in text
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_pdf_render_survives_unicode_and_empty():
    tmp = _tmpdir()
    try:
        pdf = tmp / "u.pdf"
        render_pdf("café і中文\n", pdf)   # é ok, і/中文 replaced
        assert "café" in pdf_text(pdf)
        render_pdf("", tmp / "e.pdf")                        # empty text: no crash
        assert (tmp / "e.pdf").stat().st_size > 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_pdf_wraps_unbreakable_token_and_real_guide():
    # regression: fpdf2's own wrapping aborted (WORD) or hung (CHAR) on the
    # seed guides — we pre-wrap with font metrics, so both must just work
    tmp = _tmpdir()
    try:
        long_token = "x" * 500 + "END"
        p1 = tmp / "long.pdf"
        render_pdf(f"before\n{long_token}\nafter", p1)
        text = pdf_text(p1).replace("\n", "")
        assert "END" in text and text.count("x") == 500
        slug = project_slugs()[0]
        guide = ROOT / "Data" / f"{slug}_files" / f"{slug}_GUIDE.md"
        p2 = tmp / "guide.pdf"
        render_pdf(guide.read_text(encoding="utf-8"), p2)
        assert p2.stat().st_size > 500
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_build_chat_payload_shapes():
    p = build_chat_payload("m", "sys", "hello", [], 100)
    assert p["think"] is False                      # thinking off by default
    assert p["options"] == {"temperature": 0, "num_predict": 100}
    assert [m["role"] for m in p["messages"]] == ["system", "user"]
    assert "images" not in p["messages"][1]
    p2 = build_chat_payload("m", "sys", "look", ["QUJD"], 50, think=True)
    assert p2["think"] is True
    assert p2["messages"][1]["images"] == ["QUJD"]
    p3 = build_chat_payload("m", "sys", "x", [], 10, think=None)
    assert "think" not in p3                        # omit entirely if None


def test_build_cases_all_types_with_sketch():
    slugs = project_slugs()[:2]
    sketches = _sketch_dir_for(slugs[:1])   # sketch for the first slug only
    tmp = _tmpdir()
    try:
        cases = build_cases(out_dir=tmp, limit=2, types=INPUT_TYPES,
                            sketch_dir=sketches)
        # 2 projects x (txt+md+pdf+image); slug0's image is the drawn sketch,
        # slug1 falls back to its VISUAL.png render
        assert len(cases) == 8
        by_type = {}
        for c in cases:
            by_type.setdefault(c["input_type"], []).append(c)
        img_by_slug = {c["slug"]: c for c in by_type["image"]}
        assert img_by_slug[slugs[0]]["image_source"] == "sketch"
        assert img_by_slug[slugs[1]]["image_source"] == "render"
        assert img_by_slug[slugs[1]]["input_path"].endswith("_VISUAL.png")
        for c in cases:
            p = Path(c["input_path"])
            p = p if p.is_absolute() else ROOT / p
            assert p.exists(), c["case_id"]
        # txt case content == the gold record's original_prompt
        txt = by_type["txt"][0]
        gold = json.loads((ROOT / txt["gold_path"]).read_text(encoding="utf-8"))
        body = (ROOT / txt["input_path"]).read_text(encoding="utf-8")
        assert body == gold["project"]["original_prompt"]
        # manifest was written and round-trips
        lines = (tmp / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        assert [json.loads(l) for l in lines] == cases
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(sketches, ignore_errors=True)


def test_build_default_types_txt_and_sketch_image():
    slugs = project_slugs()[:2]
    sketches = _sketch_dir_for(slugs, ext=".jpg")   # jpg sketches for both
    tmp = _tmpdir()
    try:
        assert DEFAULT_TYPES == ("txt", "image")
        cases = build_cases(out_dir=tmp, limit=2, sketch_dir=sketches)
        assert [c["input_type"] for c in cases] == ["txt", "image"] * 2
        img = next(c for c in cases if c["input_type"] == "image")
        assert img["input_path"].endswith(".jpg")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(sketches, ignore_errors=True)


def test_build_without_sketches_falls_back_to_renders():
    tmp = _tmpdir()
    empty = _tmpdir()
    try:
        cases = build_cases(out_dir=tmp, limit=2, sketch_dir=empty)
        imgs = [c for c in cases if c["input_type"] == "image"]
        assert len(imgs) == 2
        assert all(c["image_source"] == "render" for c in imgs)
        # render-sourced cases are framed as "image", not "sketch"
        text, _ = user_payload(imgs[0])
        assert "sketch" not in text
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(empty, ignore_errors=True)


def test_find_sketch_ext_priority_and_miss():
    d = _tmpdir()
    try:
        assert find_sketch("nope", d) is None
        (d / "clock.webp").write_bytes(_FAKE_PNG)
        (d / "clock.png").write_bytes(_FAKE_PNG)
        assert find_sketch("clock", d).suffix == ".png"  # png wins over webp
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_build_cases_deterministic():
    t1, t2 = _tmpdir(), _tmpdir()
    try:
        c1 = build_cases(out_dir=t1, limit=2)
        c2 = build_cases(out_dir=t2, limit=2)
        # same manifest regardless of out dir (paths inside files/ differ only
        # by the out dir, which both encode relative to ROOT — compare the rest)
        strip = lambda cs: [{k: v for k, v in c.items() if k != "input_path"}
                            for c in cs]
        assert strip(c1) == strip(c2)
        assert [c["input_type"] for c in c1] == [c["input_type"] for c in c2]
    finally:
        shutil.rmtree(t1, ignore_errors=True)
        shutil.rmtree(t2, ignore_errors=True)


def test_build_skips_project_without_gold():
    tmp = _tmpdir()
    data = tmp / "Data"
    try:
        # a project folder with a guide but NO gold record
        folder = data / "ghost_files"
        folder.mkdir(parents=True)
        (folder / "ghost_GUIDE.md").write_text("# Ghost", encoding="utf-8")
        cases = build_cases(out_dir=tmp / "out", data_dir=data)
        assert cases == []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_user_payload_shapes():
    tmp = _tmpdir()
    sketches = _sketch_dir_for(project_slugs()[:1])
    try:
        cases = build_cases(out_dir=tmp, limit=1, types=INPUT_TYPES,
                            sketch_dir=sketches)
        by_type = {c["input_type"]: c for c in cases}
        # text media -> (prompt string, no images)
        txt, imgs = user_payload(by_type["txt"])
        assert "plain-text" in txt and imgs == []
        md, _ = user_payload(by_type["md"])
        assert "markdown" in md
        pdf, _ = user_payload(by_type["pdf"])
        assert "PDF" in pdf
        # pdf content actually comes from the rendered file
        assert "Tools" in pdf or "1." in pdf
        # image -> sketch-framed text + one decodable base64 payload
        itext, iimgs = user_payload(by_type["image"])
        assert "sketch" in itext
        assert len(iimgs) == 1
        assert base64.b64decode(iimgs[0]) == _FAKE_PNG
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(sketches, ignore_errors=True)


def test_score_case_gold_scores_perfect():
    gold_path = GOLD_DIR / "digital_desk_clock.json"
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    r = score_case(json.dumps(gold, ensure_ascii=False), gold)
    assert r["parsed"] and r["valid"], r["errors"][:3]
    assert r["fp"] == 0 and r["fn"] == 0 and r["tp"] > 0


def test_score_case_garbage_and_wrong_shape():
    gold = json.loads((GOLD_DIR / "digital_desk_clock.json")
                      .read_text(encoding="utf-8"))
    r = score_case("not json at all", gold)
    assert not r["parsed"] and not r["valid"] and r["fn"] > 0
    r2 = score_case('{"components": []}', gold)
    assert r2["parsed"] and not r2["valid"] and r2["errors"]


def test_system_prompt_is_mode_b_contract():
    assert "JSON" in SYSTEM_PROMPT and "component" in SYSTEM_PROMPT


def _run_all() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run_all())
