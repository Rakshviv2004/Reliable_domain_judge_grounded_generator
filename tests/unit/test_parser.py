from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.parser import normalize_text, parse_file, text_hash

META = {"license": "public-domain", "source": "s", "title": "t", "doc_id": "x"}


def test_txt_sections_follow_headings(tmp_path: Path) -> None:
    f = tmp_path / "x.txt"
    f.write_text("# Title\n\n## Scope\nFirst scope text.\n\n## Dosing\nSecond text here.\n", encoding="utf-8")
    doc = parse_file(f, META)
    assert [s.heading for s in doc.sections] == ["Scope", "Dosing"]
    assert [s.section_id for s in doc.sections] == ["sec1", "sec2"]


def test_html_strips_boilerplate_and_keeps_headings(tmp_path: Path) -> None:
    f = tmp_path / "x.html"
    f.write_text(
        "<html><head><style>x{}</style></head><body><nav>menu</nav><h1>Main</h1><p>Body text one.</p>"
        "<h2>Dosing</h2><p>Dose text.</p><script>alert(1)</script></body></html>",
        encoding="utf-8",
    )
    doc = parse_file(f, META)
    assert [s.heading for s in doc.sections] == ["Main", "Dosing"]
    assert "menu" not in doc.full_text and "alert" not in doc.full_text


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    f = tmp_path / "x.docx"
    f.write_text("hi", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        parse_file(f, META)


def test_empty_file_raises(tmp_path: Path) -> None:
    f = tmp_path / "x.txt"
    f.write_text("   \n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="No text"):
        parse_file(f, META)


def test_text_before_first_heading_goes_to_introduction(tmp_path: Path) -> None:
    f = tmp_path / "x.txt"
    f.write_text("Some opening text.\n\n## Scope\nScope text.\n", encoding="utf-8")
    assert parse_file(f, META).sections[0].heading == "Introduction"


def test_normalization_is_idempotent_and_hash_ignores_case_and_spacing() -> None:
    raw = "Hello\r\n\r\n\r\n\r\nWorld \u00a0 again"
    assert normalize_text(normalize_text(raw)) == normalize_text(raw)
    assert text_hash("Hello  World") == text_hash("hello world")
