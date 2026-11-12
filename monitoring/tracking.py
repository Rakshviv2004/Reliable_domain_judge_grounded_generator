from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import wandb


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def init_run(job_type: str, config: dict[str, Any] | None = None, tags: list[str] | None = None) -> Any:
    """Start a W&B run tagged with the git SHA so every run maps to code + data versions."""
    return wandb.init(
        project=os.getenv("WANDB_PROJECT", "reliable-domain-judge"),
        entity=os.getenv("WANDB_ENTITY") or None,
        job_type=job_type,
        config={"git_sha": git_sha(), **(config or {})},
        tags=tags or [],
    )


def log_dataset_artifact(run: Any, name: str, path: str | Path, metadata: dict[str, Any] | None = None) -> Any:
    artifact = wandb.Artifact(name, type="dataset", metadata=metadata or {})
    p = Path(path)
    if p.is_dir():
        artifact.add_dir(str(p))
    else:
        artifact.add_file(str(p))
    run.log_artifact(artifact)
    return artifact
