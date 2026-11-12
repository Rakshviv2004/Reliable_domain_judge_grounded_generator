from ingestion.chunker import chunk_text
from ingestion.deduplicator import deduplicate


def test_chunk_text_returns_chunks():
    text = "This is a sample document. " * 20

    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_deduplicate_removes_repeated_text():
    documents = [
        "This is document one.",
        "This is document one.",
        "This is document two.",
    ]

    result = deduplicate(documents)

    assert len(result) == 2
