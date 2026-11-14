# Reliable Domain Judge + Grounded Generator

[![CI](https://github.com/Rakshviv2004/Reliable_domain_judge_grounded_generator/actions/workflows/ci.yml/badge.svg)](https://github.com/Rakshviv2004/Reliable_domain_judge_grounded_generator/actions/workflows/ci.yml)

Production-oriented AI system combining grounded RAG generation and an independently fine-tuned domain judge for evidence-based answer verification.

## How it works

1. **Grounded Generator:** answers domain questions from retrieved evidence, with citations.
2. **Reliable Domain Judge:** a separately fine-tuned model that scores each draft for faithfulness, completeness, safety and clarity, and flags unsupported claims.
3. **Orchestrator:** the generator drafts, the judge scores, and low-scoring drafts are revised (capped) or escalated to a human. Every response carries scores and sources.

The generator and judge use different base models and different training data, to limit shared blind spots.

## Project status

| Phase | Scope | Status |
|---|---|---|
| 0 | Environment, CI, DVC, W&B, corpus ingestion pipeline, tests | In progress |
| 1 | Retrieval (BM25, dense, reranker), gold set, baseline judges | Planned |
| 2 | Training datasets (SFT, preference, judge corruptions) | Planned |
| 3 | Fine-tuning (embedder, judge, generator) and ablations | Planned |
| 4 | Serving (OpenAI-compatible endpoints), orchestrator, benchmarks | Planned |
| 5 | Chaos testing, CI gates, reproducibility report | Planned |

## Repository layout

```
configs/         pipeline settings and the source registry
data/            raw, processed, gold, synthetic (versioned with DVC)
ingestion/       parse, chunk, deduplicate, split, validate
retrieval/       embeddings, BM25, vector search, reranker
generator/       generator model, prompts, training
judge/           judge model, scoring, training
orchestrator/    generate, judge, revise workflow
evaluation/      metrics and benchmarks
api/             service entry point
monitoring/      experiment tracking helpers
scripts/         command-line entry points
tests/           unit and integration tests
```

## Quickstart

Requires Python 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e .
cp .env.example .env
```

Run the corpus pipeline on a synthetic sample:

```bash
make sample
dvc add data/raw
dvc repro
make validate
```

`make sample` overwrites `configs/sources.yaml` with entries for synthetic documents. Use it only for testing, and do not run it again after you add real documents.

## Corpus ingestion

Documents go in `data/raw/`. Each file needs an entry in `configs/sources.yaml` with its title, source, URL and license. Files without an entry, or with a license outside `allowed_licenses` in `configs/ingestion.yaml`, are rejected and listed in `data/processed/rejected.json`.

The pipeline writes `documents.jsonl`, `chunks.jsonl`, `rejected.json` and `metrics.json` to `data/processed/`. Splits (train, val, test, gold) are assigned per document so no document appears in more than one split. Outputs are deterministic.

## Development

| Command | Purpose |
|---|---|
| `make format` | Format code with ruff |
| `make lint` | Lint with ruff |
| `make typecheck` | Type-check `ingestion` with mypy |
| `make test` | Run the test suite |
| `make validate` | Check the processed corpus for integrity errors |

Pre-commit hooks run on commit (`pre-commit install`). CI runs lint, format check, type check and tests on every pull request and push to `main`.

## Configuration

Copy `.env.example` to `.env`. Keep real keys out of Git, and use Codespaces secrets or your shell environment for them.

| Variable | Purpose |
|---|---|
| `WANDB_MODE` | Set to `disabled` or `offline` to run without a W&B account |
| `WANDB_PROJECT`, `WANDB_ENTITY`, `WANDB_API_KEY` | Experiment tracking |
| `HF_HOME`, `HF_TOKEN` | Hugging Face cache and token for gated models |
| `LLM_API_KEY` | Hosted model for synthetic data generation and baseline judging |

## Data versioning

Data is versioned with DVC. After cloning, run `dvc pull` to fetch it, and `dvc push` after changing it. The remote is configured in `.dvc/config`.

## License

Add a license for the code, and check each source document's own license before redistributing any corpus data.
