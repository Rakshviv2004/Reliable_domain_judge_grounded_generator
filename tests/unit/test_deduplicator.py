from __future__ import annotations

from collections.abc import Callable

from ingestion.config import DedupConfig
from ingestion.deduplicator import dedupe_chunks, dedupe_documents
from ingestion.schemas import Chunk, Document

BASE = " ".join(f"w{i}" for i in range(300))
OTHER = " ".join(f"x{i}" for i in range(300))
CFG = DedupConfig()


def test_exact_duplicate_dropped(make_doc: Callable[[str, str], Document]) -> None:
    kept, dropped = dedupe_documents([make_doc("a", BASE), make_doc("b", BASE.upper())], CFG)
    assert [d.doc_id for d in kept] == ["a"]
    assert dropped[0]["reason"] == "exact_duplicate"


def test_near_duplicate_dropped(make_doc: Callable[[str, str], Document]) -> None:
    kept, dropped = dedupe_documents([make_doc("a", BASE), make_doc("b", BASE.replace("w150", "zzz"))], CFG)
    assert [d.doc_id for d in kept] == ["a"]
    assert dropped[0] == {"doc_id": "b", "reason": "near_duplicate", "duplicate_of": "a"}


def test_distinct_documents_kept(make_doc: Callable[[str, str], Document]) -> None:
    kept, dropped = dedupe_documents([make_doc("a", BASE), make_doc("b", OTHER)], CFG)
    assert len(kept) == 2 and dropped == []


def test_result_is_independent_of_input_order(make_doc: Callable[[str, str], Document]) -> None:
    docs = [make_doc("a", BASE), make_doc("b", BASE)]
    kept1, _ = dedupe_documents(docs, CFG)
    kept2, _ = dedupe_documents(list(reversed(docs)), CFG)
    assert [d.doc_id for d in kept1] == [d.doc_id for d in kept2] == ["a"]


def test_duplicate_chunks_removed() -> None:
    def chunk(cid: str, text: str) -> Chunk:
        return Chunk(
            chunk_id=cid,
            doc_id="d",
            section_id="s",
            heading="h",
            text=text,
            n_words=2,
            split="train",
            license="l",
            source="s",
        )

    out, n = dedupe_chunks([chunk("d#s#p1", "same text"), chunk("d#s#p2", "Same  Text"), chunk("d#s#p3", "other")])
    assert n == 1 and [c.chunk_id for c in out] == ["d#s#p1", "d#s#p3"]
