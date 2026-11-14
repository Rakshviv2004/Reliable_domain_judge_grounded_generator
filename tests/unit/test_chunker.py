from __future__ import annotations

import re
from collections.abc import Callable

from ingestion.chunker import chunk_document
from ingestion.config import ChunkConfig
from ingestion.schemas import Document

SENT = "Sentence number {} has exactly seven words."


def _doc(make_doc: Callable[[str, str], Document], n: int = 100) -> Document:
    return make_doc("doc1", " ".join(SENT.format(i) for i in range(n)))


def test_chunks_respect_target_size(make_doc: Callable[[str, str], Document]) -> None:
    chunks = chunk_document(_doc(make_doc), ChunkConfig(target_words=50, overlap_words=14))
    assert len(chunks) > 1
    assert all(c.n_words <= 50 for c in chunks)


def test_consecutive_chunks_overlap(make_doc: Callable[[str, str], Document]) -> None:
    chunks = chunk_document(_doc(make_doc), ChunkConfig(target_words=50, overlap_words=14))
    pattern = r"Sentence number \d+ has exactly seven words\."
    for a, b in zip(chunks, chunks[1:], strict=False):
        assert re.findall(pattern, a.text)[-1] in b.text


def test_no_sentence_is_lost(make_doc: Callable[[str, str], Document]) -> None:
    chunks = chunk_document(_doc(make_doc), ChunkConfig(target_words=50, overlap_words=14))
    joined = " ".join(c.text for c in chunks)
    assert all(SENT.format(i) in joined for i in range(100))


def test_ids_are_unique_and_well_formed(make_doc: Callable[[str, str], Document]) -> None:
    chunks = chunk_document(_doc(make_doc), ChunkConfig(target_words=50, overlap_words=14))
    ids = [c.chunk_id for c in chunks]
    assert len(set(ids)) == len(ids)
    assert ids[0] == "doc1#sec1#p1"


def test_short_section_gives_single_chunk(make_doc: Callable[[str, str], Document]) -> None:
    chunks = chunk_document(_doc(make_doc, n=3), ChunkConfig())
    assert len(chunks) == 1 and chunks[0].split == "train"
