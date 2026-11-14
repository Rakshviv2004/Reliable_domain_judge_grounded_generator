from __future__ import annotations

import argparse
import json
import logging
import os

from dotenv import load_dotenv

from ingestion.config import load_config
from ingestion.pipeline import run_ingestion


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/ingestion.yaml")
    parser.add_argument("--wandb", action="store_true", help="log stats and dataset artifact to W&B")
    args = parser.parse_args()

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    cfg = load_config(args.config)
    stats = run_ingestion(cfg)
    print(json.dumps(stats, indent=2))

    if args.wandb:
        from monitoring.tracking import init_run, log_dataset_artifact

        run = init_run("ingest", config=cfg.model_dump(mode="json"))
        run.log(stats)
        log_dataset_artifact(run, "corpus-processed", cfg.processed_dir, metadata=stats)
        run.finish()


if __name__ == "__main__":
    main()
