"""Read-only example catalog boundary."""
from typing import Protocol


class ComparisonCatalog(Protocol):
    def records(self) -> list[dict]: ...
    def get(self, example_id: str) -> dict | None: ...


class ComparisonRenderer(Protocol):
    def __call__(self, view: dict) -> str: ...
