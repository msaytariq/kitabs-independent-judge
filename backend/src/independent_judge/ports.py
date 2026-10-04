"""Interfaces used by application services; no infrastructure imports."""
from typing import Protocol

from independent_judge.domain.inputs import Comparison, ExtractedText, InputTriple


class TextExtractor(Protocol):
    def extract(self, content: bytes, filename: str, content_type: str) -> ExtractedText: ...


class ComparisonRepository(Protocol):
    def create(self, inputs: InputTriple) -> str: ...

    def get(self, comparison_id: str) -> Comparison | None: ...


class ScopeRepository(Protocol):
    def create(self, snapshot: dict) -> dict: ...

    def get(self, scope_id: str) -> dict | None: ...
