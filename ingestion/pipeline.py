from __future__ import annotations

import json
import logging
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from ingestion.chunker import chunk_document
from ingestion.config import IngestionConfig
from ingestion.deduplicator import dedupe_chunks, dedupe_documents
from ingestion.parser import SUPPORTED, parse_file, slugify
from ingestion.schemas import Chunk, Document
from ingestion.splitter import assign_split

log = logging.getLogger(__name__)


def load_sources(path: Path) -> dict[str, dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {s["file"]: s for s in data.get("sources", [])}


def _write_jsonl(path: Path, rows: Sequence[BaseModel]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(row.model_dump_json() + "\n")


def run_ingestion(cfg: IngestionConfig) -> dict[str, Any]:
    sources = load_sources(cfg.sources_file)
    docs: list[Document] = []
    rejected: list[dict[str, str]] = []
    n_files = 0

    for path in sorted(cfg.raw_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:
            continue
        n_files += 1
        rel = path.relative_to(cfg.raw_dir).as_posix()
        meta = sources.get(rel)
        if meta is None:
            rejected.append({"file": rel, "reason": "missing_metadata"})
            continue
        if meta.get("license") not in cfg.allowed_licenses:
            rejected.append({"file": rel, "reason": f"license_not_allowed:{meta.get('license')}"})
            continue
        meta = {**meta, "doc_id": meta.get("doc_id") or slugify(Path(rel).with_suffix("").as_posix())}
        try:
            docs.append(parse_file(path, meta))
        except Exception as exc:  # one bad file must not stop the run
            log.warning("Failed to parse %s: %s", rel, exc)
            rejected.append({"file": rel, "reason": f"parse_error:{exc}"})

    kept, duplicates = dedupe_documents(docs, cfg.dedup)
    for doc in kept:
        doc.split = assign_split(doc.doc_id, cfg.split)

    chunks: list[Chunk] = []
    for doc in kept:
        chunks.extend(chunk_document(doc, cfg.chunk))
    chunks, n_dup_chunks = dedupe_chunks(chunks)

    kept.sort(key=lambda d: d.doc_id)
    chunks.sort(key=lambda c: c.chunk_id)

    out = cfg.processed_dir
    out.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out / "documents.jsonl", kept)
    _write_jsonl(out / "chunks.jsonl", chunks)
    (out / "rejected.json").write_text(
        json.dumps({"rejected": rejected, "duplicates": duplicates}, indent=2, sort_keys=True), encoding="utf-8"
    )

    stats: dict[str, Any] = {
        "files_found": n_files,
        "documents_parsed": len(docs),
        "documents_rejected": len(rejected),
        "documents_duplicate": len(duplicates),
        "documents_kept": len(kept),
        "chunks": len(chunks),
        "chunks_duplicate": n_dup_chunks,
        "docs_per_split": dict(sorted(Counter(str(d.split) for d in kept).items())),
        "chunks_per_split": dict(sorted(Counter(c.split for c in chunks).items())),
        "mean_chunk_words": round(sum(c.n_words for c in chunks) / max(len(chunks), 1), 1),
    }
    (out / "metrics.json").write_text(json.dumps(stats, indent=2, sort_keys=True), encoding="utf-8")
    log.info("Ingestion complete: %s", stats)
    return stats
