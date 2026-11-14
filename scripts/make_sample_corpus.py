from __future__ import annotations

import random
from pathlib import Path

import yaml

TOPICS = [
    "hypertension",
    "type 2 diabetes",
    "asthma",
    "kidney disease",
    "heart failure",
    "hypothyroidism",
    "migraine",
    "osteoarthritis",
]
VOCAB = (
    "patient dose therapy risk monitor review evidence outcome baseline assessment threshold referral renal hepatic "
    "cardiac screening followup adverse symptom clinic dosage response trial cohort marker target adjust interval "
    "history lifestyle diet exercise adherence adults older younger severe mild moderate stable acute chronic "
    "measure record repeat confirm exclude consider avoid combine switch continue withdraw titrate review audit"
).split()


def sentences(rng: random.Random, n: int) -> str:
    return " ".join(" ".join(rng.choices(VOCAB, k=12)).capitalize() + "." for _ in range(n))


def build(topic: str) -> str:
    rng = random.Random(topic)
    return (
        f"# {topic.title()} sample guideline\n\n"
        f"## Scope\n\n{sentences(rng, 8)}\n\n"
        f"## Recommendations\n\n{sentences(rng, 30)}\n\n"
        f"## Monitoring\n\n{sentences(rng, 8)}\n"
    )


def main() -> None:
    raw = Path("data/raw/sample")
    raw.mkdir(parents=True, exist_ok=True)
    sources = []

    def add(name: str, text: str, license_: str = "public-domain", with_meta: bool = True) -> None:
        (raw / name).write_text(text, encoding="utf-8", newline="\n")
        if with_meta:
            sources.append(
                {
                    "file": f"sample/{name}",
                    "title": name,
                    "source": "Synthetic Sample",
                    "url": f"https://example.org/{name}",
                    "license": license_,
                }
            )

    for t in TOPICS:
        add(f"{t.replace(' ', '_')}.txt", build(t))
    add("hypertension_copy.txt", build("hypertension"))  # exact duplicate
    add("type_2_diabetes_amended.txt", build("type 2 diabetes") + "\nAmended edition note.\n")  # near duplicate
    add("proprietary_doc.txt", build("sepsis"), license_="proprietary")  # disallowed license
    add("orphan_doc.txt", build("copd"), with_meta=False)  # missing metadata

    Path("configs").mkdir(exist_ok=True)
    Path("configs/sources.yaml").write_text(yaml.safe_dump({"sources": sources}, sort_keys=False), encoding="utf-8")
    print(f"Wrote {len(list(raw.glob('*.txt')))} sample files and configs/sources.yaml")


if __name__ == "__main__":
    main()
