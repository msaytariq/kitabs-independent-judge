"""Immutable original inputs and draft comparisons."""
from dataclasses import dataclass, field
from typing import Literal

Role = Literal["source", "a", "b"]
MAX_FILE_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class ExtractedText:
    text: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class MaterialInput:
    id: str
    role: Role
    text: str
    sha256: str
    filename: str
    file_sha256: str
    content_type: str
    content: bytes = field(repr=False)
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class InputTriple:
    source: MaterialInput
    a: MaterialInput
    b: MaterialInput
    source_language: str
    target_language: str

    @property
    def materials(self) -> tuple[MaterialInput, MaterialInput, MaterialInput]:
        return self.source, self.a, self.b


@dataclass(frozen=True)
class Comparison:
    id: str
    inputs: InputTriple
    created_at: str
    status: Literal["draft"] = "draft"
