from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import pdfplumber
from bs4 import BeautifulSoup

from ingestion.schemas import Document, Section

SUPPORTED = {".txt", ".md", ".html", ".htm", ".pdf"}
_NUM_HEADING = re.compile(r"^\d+(\.\d+)*\.?\s+[A-Z][^.!?]{2,80}$")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def text_hash(text: str) -> str:
    """Whitespace- and case-insensitive content hash used for exact deduplication."""
    return hashlib.sha256(" ".join(text.lower().split()).encode("utf-8")).hexdigest()


def _split_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading = "Introduction"
    buf: list[str] = []
    for line in text.split("\n"):
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            if "".join(buf).strip():
                sections.append((heading, "\n".join(buf).strip()))
            heading, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((heading, "\n".join(buf).strip()))
    return sections


def _html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    lines: list[str] = []
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        lines.append(f"{'#' * int(el.name[1])} {text}" if el.name.startswith("h") else text)
        lines.append("")
    return "\n".join(lines)


def _pdf_to_markdown(path: Path) -> str:
    lines: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").split("\n"):
                line = line.strip()
                lines.append(f"## {line}" if _NUM_HEADING.match(line) else line)
    return "\n".join(lines)


def parse_file(path: Path, meta: dict[str, Any]) -> Document:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"Unsupported file type: {suffix}")
    if suffix == ".pdf":
        raw = _pdf_to_markdown(path)
    elif suffix in {".html", ".htm"}:
        raw = _html_to_markdown(path.read_text(encoding="utf-8-sig", errors="ignore"))
    else:
        raw = path.read_text(encoding="utf-8-sig", errors="ignore")
    text = normalize_text(raw)
    pairs = _split_sections(text)
    if not pairs:
        raise ValueError(f"No text extracted from {path.name}")
    return Document(
        doc_id=meta.get("doc_id") or slugify(path.stem),
        title=meta.get("title", path.stem),
        source=meta.get("source", "unknown"),
        url=meta.get("url"),
        license=meta["license"],
        published=meta.get("published"),
        sha256=text_hash(text),
        sections=[Section(section_id=f"sec{i + 1}", heading=h, text=b) for i, (h, b) in enumerate(pairs)],
    )
