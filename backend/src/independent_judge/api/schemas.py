"""HTTP models and deliberate public projection, excluding original byte blobs."""
from typing import Literal
from pydantic import BaseModel, ConfigDict

from independent_judge.domain.inputs import Comparison


class TextInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    a: str
    b: str
    source_language: str
    target_language: str


class MaterialView(BaseModel):
    id: str
    role: Literal["source", "a", "b"]
    text: str
    sha256: str
    file_sha256: str
    filename: str
    content_type: str
    warnings: tuple[str, ...]
    page_count: int | None
    provenance: dict


class ComparisonView(BaseModel):
    id: str
    status: Literal["draft"]
    created_at: str
    source_language: str
    target_language: str
    materials: dict[str, MaterialView]

    @classmethod
    def from_comparison(cls, comparison: Comparison) -> "ComparisonView":
        return cls(
            id=comparison.id, status=comparison.status, created_at=comparison.created_at,
            source_language=comparison.inputs.source_language,
            target_language=comparison.inputs.target_language,
            materials={m.role: MaterialView(**{name: getattr(m, name) for name in MaterialView.model_fields})
                       for m in comparison.inputs.materials},
        )
