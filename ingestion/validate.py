from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_processed(processed_dir: Path, allowed_licenses: list[str]) -> list[str]:
    """Return a list of integrity errors (empty list means the corpus is valid)."""
    errors: list[str] = []
    docs = _read_jsonl(processed_dir / "documents.jsonl")
    chunks = _read_jsonl(processed_dir / "chunks.jsonl")

    doc_split = {d["doc_id"]: d["split"] for d in docs}
    if len(doc_split) != len(docs):
        errors.append("duplicate doc_id in documents.jsonl")
    if len({c["chunk_id"] for c in chunks}) != len(chunks):
        errors.append("duplicate chunk_id in chunks.jsonl")

    for d in docs:
        if d["split"] not in {"train", "val", "test", "gold"}:
            errors.append(f"invalid split for document {d['doc_id']}: {d['split']}")
        if d["license"] not in allowed_licenses:
            errors.append(f"disallowed license for document {d['doc_id']}: {d['license']}")

    for c in chunks:
        if c["doc_id"] not in doc_split:
            errors.append(f"orphan chunk {c['chunk_id']}")
        elif c["split"] != doc_split[c["doc_id"]]:
            errors.append(
                f"split leakage: chunk {c['chunk_id']} is {c['split']} but its document is {doc_split[c['doc_id']]}"
            )
        if not c["text"].strip():
            errors.append(f"empty chunk {c['chunk_id']}")
    return errors
