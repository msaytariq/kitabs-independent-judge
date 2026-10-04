"""Compose local adapters; no provider or platform runtime is loaded."""
import os
from pathlib import Path

from independent_judge.application.intake import IntakeService
from independent_judge.infrastructure.sqlite_repository import SqliteComparisonRepository
from independent_judge.infrastructure.text_extractors import LocalTextExtractor


def build_intake(data_dir: Path | None = None) -> IntakeService:
    directory = Path(data_dir) if data_dir is not None else Path(os.environ.get("JUDGE_DATA_DIR", ".judge-data"))
    return IntakeService(LocalTextExtractor(), SqliteComparisonRepository(directory.resolve()))
