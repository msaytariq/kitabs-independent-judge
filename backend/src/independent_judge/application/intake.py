"""Validate and extract all three inputs before storing a draft atomically."""
from dataclasses import dataclass
from hashlib import sha256
import re
from uuid import uuid4

from independent_judge.domain.errors import InputError
from independent_judge.domain.inputs import MAX_FILE_BYTES, Comparison, InputTriple, MaterialInput
from independent_judge.ports import ComparisonRepository, TextExtractor


@dataclass(frozen=True)
class Upload:
    content: bytes
    filename: str
    content_type: str = "application/octet-stream"


def _language(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", value) or len(value) > 64:
        raise InputError("invalid_language", "Choose a valid language code, such as ar or en.")
    return value


class IntakeService:
    def __init__(self, extractor: TextExtractor, repository: ComparisonRepository):
        self.extractor = extractor
        self.repository = repository

    def create(self, source: Upload, a: Upload, b: Upload,
               source_language: str, target_language: str) -> Comparison:
        source_language, target_language = _language(source_language), _language(target_language)
        uploads = (source, a, b)
        # Inspect the entire triple before running any format parser.
        for item in uploads:
            if len(item.content) > MAX_FILE_BYTES:
                raise InputError("file_too_large", "Each file must be at most 20 MiB.")
        materials = []
        for role, item in zip(("source", "a", "b"), uploads, strict=True):
            name = item.filename.replace("\\", "/").rsplit("/", 1)[-1]
            if not name or len(name) > 255 or any(ord(c) < 32 for c in name):
                raise InputError("invalid_filename", "Provide a file with a valid filename.")
            extracted = self.extractor.extract(item.content, name, item.content_type)
            if not extracted.text.strip():
                raise InputError("empty_text", "The document has no usable text. Check the file before comparison.")
            materials.append(MaterialInput(
                id=uuid4().hex, role=role, text=extracted.text,
                sha256=sha256(extracted.text.encode("utf-8")).hexdigest(), filename=name,
                file_sha256=sha256(item.content).hexdigest(), content_type=item.content_type,
                content=item.content, warnings=extracted.warnings,
            ))
        inputs = InputTriple(*materials, source_language=source_language, target_language=target_language)
        comparison_id = self.repository.create(inputs)
        comparison = self.repository.get(comparison_id)
        if comparison is None:
            raise RuntimeError("Stored comparison could not be read back")
        return comparison

    def get(self, comparison_id: str) -> Comparison:
        comparison = self.repository.get(comparison_id)
        if comparison is None:
            raise InputError("comparison_not_found", "Comparison not found.")
        return comparison
