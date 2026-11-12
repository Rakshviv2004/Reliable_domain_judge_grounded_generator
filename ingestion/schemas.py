from __future__ import annotations

from pydantic import BaseModel


class Section(BaseModel):
    section_id: str
    heading: str
    text: str


class Document(BaseModel):
    doc_id: str
    title: str
    source: str
    url: str | None = None
    license: str
    published: str | None = None
    sha256: str
    sections: list[Section]
    split: str | None = None

    @property
    def full_text(self) -> str:
        return "\n\n".join(s.text for s in self.sections)


class Chunk(BaseModel):
    chunk_id: str  # <doc_id>#<section_id>#p<n>
    doc_id: str
    section_id: str
    heading: str
    text: str
    n_words: int
    split: str
    license: str
    source: str
