"""Retrieval boundary; the domain never opens a network connection."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RetrievedDocument:
    content: bytes
    filename: str
    content_type: str
    provenance: dict


class DocumentRetriever(Protocol):
    def fetch(self, url: str) -> RetrievedDocument: ...
