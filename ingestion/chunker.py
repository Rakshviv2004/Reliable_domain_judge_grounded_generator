from __future__ import annotations

import re

from ingestion.config import ChunkConfig
from ingestion.schemas import Chunk, Document

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_END.split(" ".join(text.split())) if s.strip()]


def chunk_text(text: str, target_words: int, overlap_words: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in split_sentences(text):
        n = len(sentence.split())
        if current and current_words + n > target_words:
            chunks.append(" ".join(current))
            carry: list[str] = []
            carried = 0
            for prev in reversed(current):
                w = len(prev.split())
                if carried + w > overlap_words:
                    break
                carry.insert(0, prev)
                carried += w
            current, current_words = carry, carried
        current.append(sentence)
        current_words += n
    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_document(doc: Document, cfg: ChunkConfig) -> list[Chunk]:
    if doc.split is None:
        raise ValueError("Assign a split before chunking so chunks inherit it.")
    out: list[Chunk] = []
    for section in doc.sections:
        for i, text in enumerate(chunk_text(section.text, cfg.target_words, cfg.overlap_words), start=1):
            out.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}#{section.section_id}#p{i}",
                    doc_id=doc.doc_id,
                    section_id=section.section_id,
                    heading=section.heading,
                    text=text,
                    n_words=len(text.split()),
                    split=doc.split,
                    license=doc.license,
                    source=doc.source,
                )
            )
    return out
