from __future__ import annotations

import pytest
from pydantic import ValidationError

from ingestion.config import SplitConfig
from ingestion.splitter import assign_split


def test_assignment_is_deterministic() -> None:
    cfg = SplitConfig()
    assert assign_split("doc-1", cfg) == assign_split("doc-1", cfg)


def test_proportions_are_close_to_config() -> None:
    cfg = SplitConfig()
    n = 5000
    counts: dict[str, int] = {}
    for i in range(n):
        s = assign_split(f"doc-{i}", cfg)
        counts[s] = counts.get(s, 0) + 1
    for name, pct in (("train", 70), ("val", 10), ("test", 10), ("gold", 10)):
        assert abs(counts[name] / n - pct / 100) < 0.03


def test_seed_changes_assignment() -> None:
    a = [assign_split(f"d{i}", SplitConfig(seed="v1")) for i in range(200)]
    b = [assign_split(f"d{i}", SplitConfig(seed="v2")) for i in range(200)]
    assert a != b


def test_percentages_must_sum_to_100() -> None:
    with pytest.raises(ValidationError):
        SplitConfig(train=60, val=10, test=10, gold=10)
