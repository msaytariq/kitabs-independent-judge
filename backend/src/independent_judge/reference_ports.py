"""Read-only reference library boundary."""
from typing import Protocol


class LibraryUnavailable(RuntimeError):
    pass


class HadithLibraryPort(Protocol):
    def records(self) -> list[dict]: ...
