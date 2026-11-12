from __future__ import annotations

import hashlib

from ingestion.config import SplitConfig


def assign_split(doc_id: str, cfg: SplitConfig) -> str:
    bucket = int(hashlib.sha256(f"{cfg.seed}:{doc_id}".encode()).hexdigest()[:8], 16) % 100
    cumulative = 0
    for name, pct in (("train", cfg.train), ("val", cfg.val), ("test", cfg.test), ("gold", cfg.gold)):
        cumulative += pct
        if bucket < cumulative:
            return name
    raise AssertionError("unreachable: split percentages sum to 100")
