"""Read private, versioned example packets from this stand's data directory."""
import json
from pathlib import Path
import re
from independent_judge.domain.errors import InputError


class FileComparisonCatalog:
    def __init__(self, directory: Path):
        self.directory = (directory / 'comparison-catalog').resolve()
        self.evidence_directory = (directory / 'apparatus-evidence').resolve()
        self.review_directory = (directory / 'source-reviews').resolve()

    def get(self, example_id: str) -> dict | None:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', example_id): return None
        path = self.directory / f'{example_id}.json'
        if not path.is_file() or path.resolve().parent != self.directory: return None
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if data['id'] != example_id: raise ValueError('identity')
            evidence = self.evidence_directory / f'{example_id}.json'
            if evidence.is_file() and evidence.resolve().parent == self.evidence_directory:
                data['capability_evidence'] = json.loads(evidence.read_text(encoding='utf-8'))
            review = self.review_directory / f'{example_id}.json'
            if review.is_file() and review.resolve().parent == self.review_directory:
                data['source_review'] = json.loads(review.read_text(encoding='utf-8'))
            return data
        except (ValueError, KeyError, TypeError) as exc:
            raise InputError('invalid_catalog', 'Паспорт примера повреждён.') from exc

    def records(self) -> list[dict]:
        return [record for path in sorted(self.directory.glob('*.json'))
                if (record := self.get(path.stem)) is not None]
