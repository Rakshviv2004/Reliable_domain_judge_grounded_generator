from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from ingestion.config import IngestionConfig
from ingestion.parser import text_hash
from ingestion.schemas import Document, Section


@pytest.fixture
def make_text() -> Callable[[str, int], str]:
    def _make(prefix: str, n: int) -> str:
        return " ".join(f"{prefix}{i} reports outcome {i} in adults." for i in range(n))

    return _make


@pytest.fixture
def make_doc() -> Callable[[str, str], Document]:
    def _make(doc_id: str, text: str) -> Document:
        return Document(
            doc_id=doc_id,
            title=doc_id,
            source="test",
            license="public-domain",
            sha256=text_hash(text),
            sections=[Section(section_id="sec1", heading="Body", text=text)],
            split="train",
        )

    return _make


@pytest.fixture
def corpus(tmp_path: Path, make_text: Callable[[str, int], str]) -> IngestionConfig:
    raw = tmp_path / "raw"
    raw.mkdir()

    def body(prefix: str) -> str:
        return f"# Title\n\n## Scope\n\n{make_text(prefix, 60)}\n\n## Advice\n\n{make_text(prefix + 'b', 60)}\n"

    for name, prefix in [
        ("a.txt", "alpha"),
        ("a_copy.txt", "alpha"),
        ("b.txt", "beta"),
        ("c.txt", "gamma"),
        ("d.txt", "delta"),
    ]:
        (raw / name).write_text(body(prefix), encoding="utf-8")

    def entry(file: str, license_: str = "public-domain") -> dict[str, str]:
        return {"file": file, "source": "S", "license": license_, "title": file}

    sources = {
        "sources": [entry("a.txt"), entry("a_copy.txt"), entry("b.txt"), entry("c.txt", "proprietary")]
    }  # d.txt has none
    (tmp_path / "sources.yaml").write_text(yaml.safe_dump(sources), encoding="utf-8")
    return IngestionConfig(
        raw_dir=raw,
        processed_dir=tmp_path / "processed",
        sources_file=tmp_path / "sources.yaml",
        allowed_licenses=["public-domain"],
    )
