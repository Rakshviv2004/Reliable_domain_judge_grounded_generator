
.PHONY: sample validate repro

sample:
	python scripts/make_sample_corpus.py

validate:
	python scripts/validate_corpus.py

repro:
	dvc repro
