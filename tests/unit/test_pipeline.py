from __future__ import annotations

import json
from pathlib import Path

from ingestion.config import IngestionConfig
from ingestion.pipeline import run_ingestion
from ingestion.validate import validate_processed


def test_pipeline_filters_dedupes_and_counts(corpus: IngestionConfig) -> None:
    stats = run_ingestion(corpus)
    assert stats["files_found"] == 5
    assert stats["documents_parsed"] == 3  # a, a_copy, b (c and d rejected before parsing)
    assert stats["documents_rejected"] == 2  # c: license, d: missing metadata
    assert stats["documents_duplicate"] == 1  # a_copy
    assert stats["documents_kept"] == 2
    assert stats["chunks"] > 2


def test_rejection_reasons_are_recorded(corpus: IngestionConfig) -> None:
    run_ingestion(corpus)
    report = json.loads((corpus.processed_dir / "rejected.json").read_text(encoding="utf-8"))
    reasons = {r["file"]: r["reason"] for r in report["rejected"]}
    assert reasons["c.txt"].startswith("license_not_allowed")
    assert reasons["d.txt"] == "missing_metadata"
    assert report["duplicates"][0]["duplicate_of"] == "a"


def test_output_passes_validation(corpus: IngestionConfig) -> None:
    run_ingestion(corpus)
    assert validate_processed(corpus.processed_dir, corpus.allowed_licenses) == []


def test_chunks_inherit_document_split(corpus: IngestionConfig) -> None:
    run_ingestion(corpus)
    rows = lambda name: [json.loads(x) for x in (corpus.processed_dir / name).read_text(encoding="utf-8").splitlines()]  # noqa: E731
    doc_split = {d["doc_id"]: d["split"] for d in rows("documents.jsonl")}
    assert all(c["split"] == doc_split[c["doc_id"]] for c in rows("chunks.jsonl"))


def test_output_is_byte_for_byte_deterministic(corpus: IngestionConfig, tmp_path: Path) -> None:
    run_ingestion(corpus)
    second = corpus.model_copy(update={"processed_dir": tmp_path / "processed2"})
    run_ingestion(second)
    for name in ("documents.jsonl", "chunks.jsonl", "metrics.json"):
        assert (corpus.processed_dir / name).read_bytes() == (second.processed_dir / name).read_bytes()


def test_validator_detects_split_leakage(corpus: IngestionConfig) -> None:
    run_ingestion(corpus)
    path = corpus.processed_dir / "chunks.jsonl"
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["split"] = "gold" if rows[0]["split"] != "gold" else "train"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    assert any("split leakage" in e for e in validate_processed(corpus.processed_dir, corpus.allowed_licenses))
