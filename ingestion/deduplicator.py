from __future__ import annotations

from datasketch import MinHash, MinHashLSH

from ingestion.config import DedupConfig
from ingestion.parser import text_hash
from ingestion.schemas import Chunk, Document


def _minhash(text: str, shingle_size: int, num_perm: int) -> MinHash:
    words = text.lower().split()
    if len(words) < shingle_size:
        shingles = {" ".join(words)}
    else:
        shingles = {" ".join(words[i : i + shingle_size]) for i in range(len(words) - shingle_size + 1)}
    mh = MinHash(num_perm=num_perm)
    for s in shingles:
        mh.update(s.encode("utf-8"))
    return mh


def dedupe_documents(docs: list[Document], cfg: DedupConfig) -> tuple[list[Document], list[dict[str, str]]]:
    """Drop exact and near-duplicate documents. Sorted by doc_id so results are deterministic."""
    lsh = MinHashLSH(threshold=cfg.near_dup_threshold, num_perm=cfg.num_perm)
    seen_hash: dict[str, str] = {}
    kept: list[Document] = []
    dropped: list[dict[str, str]] = []
    for doc in sorted(docs, key=lambda d: d.doc_id):
        if doc.sha256 in seen_hash:
            dropped.append({"doc_id": doc.doc_id, "reason": "exact_duplicate", "duplicate_of": seen_hash[doc.sha256]})
            continue
        mh = _minhash(doc.full_text, cfg.shingle_size, cfg.num_perm)
        matches = lsh.query(mh)
        if matches:
            dropped.append({"doc_id": doc.doc_id, "reason": "near_duplicate", "duplicate_of": sorted(matches)[0]})
            continue
        lsh.insert(doc.doc_id, mh)
        seen_hash[doc.sha256] = doc.doc_id
        kept.append(doc)
    return kept, dropped


def dedupe_chunks(chunks: list[Chunk]) -> tuple[list[Chunk], int]:
    seen: set[str] = set()
    out: list[Chunk] = []
    for c in sorted(chunks, key=lambda c: c.chunk_id):
        key = text_hash(c.text)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out, len(chunks) - len(out)
