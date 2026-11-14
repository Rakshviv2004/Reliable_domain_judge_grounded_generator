from __future__ import annotations

import sys

from dotenv import load_dotenv

from ingestion.config import load_config
from ingestion.validate import validate_processed


def main() -> int:
    load_dotenv()
    cfg = load_config()
    errors = validate_processed(cfg.processed_dir, cfg.allowed_licenses)
    for e in errors[:50]:
        print("FAIL:", e)
    if errors:
        print(f"{len(errors)} validation error(s)")
        return 1
    print("Corpus validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
