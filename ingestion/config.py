from __future__ import annotations

from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, Field, model_validator


class ChunkConfig(BaseModel):
    target_words: int = 250
    overlap_words: int = 40


class DedupConfig(BaseModel):
    near_dup_threshold: float = 0.85
    shingle_size: int = 5
    num_perm: int = 128


class SplitConfig(BaseModel):
    train: int = 70
    val: int = 10
    test: int = 10
    gold: int = 10
    seed: str = "v1"

    @model_validator(mode="after")
    def _sums_to_100(self) -> Self:
        if self.train + self.val + self.test + self.gold != 100:
            raise ValueError("split percentages must sum to 100")
        return self


class IngestionConfig(BaseModel):
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    sources_file: Path = Path("configs/sources.yaml")
    allowed_licenses: list[str]
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    dedup: DedupConfig = Field(default_factory=DedupConfig)
    split: SplitConfig = Field(default_factory=SplitConfig)


def load_config(path: str | Path = "configs/ingestion.yaml") -> IngestionConfig:
    with open(path, encoding="utf-8") as f:
        return IngestionConfig(**yaml.safe_load(f))
