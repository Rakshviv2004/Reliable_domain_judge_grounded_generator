from __future__ import annotations

from ingestion.chunker import chunk_text
from ingestion.config import DedupConfig
from ingestion.deduplicator import dedupe_documents
from ingestion.parser import text_hash
from ingestion.schemas import Document, Section


def _doc(doc_id: str, text: str) -> Document:
    return Document(
        doc_id=doc_id,
        title=doc_id,
        source="test",
        license="public-domain",
        sha256=text_hash(text),
        sections=[Section(section_id="sec1", heading="Body", text=text)],
        split="train",
    )


def test_chunk_text_returns_chunks() -> None:
    text = "This is a sample document. " * 20  # 20 sentences, 5 words each

    chunks = chunk_text(text, target_words=50, overlap_words=10)

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk.split()) <= 50 for chunk in chunks)


def test_dedupe_documents_removes_repeated_text() -> None:
    documents = [
        _doc("1", "This is document one."),
        _doc("2", "This is document one."),
        _doc("3", "This is document two."),
    ]

    kept, dropped = dedupe_documents(documents, DedupConfig())

    assert [d.doc_id for d in kept] == ["1", "3"]
    assert dropped == [{"doc_id": "2", "reason": "exact_duplicate", "duplicate_of": "1"}]
