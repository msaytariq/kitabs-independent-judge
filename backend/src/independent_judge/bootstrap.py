"""Compose local adapters; no provider or platform runtime is loaded."""
import os
from pathlib import Path

from independent_judge.application.intake import IntakeService
from independent_judge.infrastructure.sqlite_repository import SqliteComparisonRepository
from independent_judge.infrastructure.text_extractors import LocalTextExtractor
from independent_judge.application.prepare_scope import ScopeService
from independent_judge.infrastructure.scope_repository import SqliteScopeRepository
from independent_judge.application.editorial_review import EditorialService
from independent_judge.infrastructure.editorial_repository import SqliteEditorialRepository
from independent_judge.application.comparison_view import ComparisonViewService
from independent_judge.infrastructure.comparison_catalog import FileComparisonCatalog
from independent_judge.infrastructure.comparison_report import comparison_html


def data_directory(data_dir: Path | None = None) -> Path:
    directory = Path(data_dir) if data_dir is not None else Path(os.environ.get("JUDGE_DATA_DIR", ".judge-data"))
    return directory.resolve()


def build_intake(data_dir: Path | None = None) -> IntakeService:
    return IntakeService(LocalTextExtractor(), SqliteComparisonRepository(data_directory(data_dir)))


def build_scope(data_dir: Path | None = None) -> ScopeService:
    directory = data_directory(data_dir)
    return ScopeService(SqliteComparisonRepository(directory), SqliteScopeRepository(directory))


def build_editorial(data_dir: Path | None = None) -> EditorialService:
    directory=data_directory(data_dir)
    return EditorialService(SqliteScopeRepository(directory),SqliteEditorialRepository(directory))


def build_comparison_view(data_dir: Path | None = None, jobs=None) -> ComparisonViewService:
    directory = data_directory(data_dir)
    return ComparisonViewService(FileComparisonCatalog(directory), SqliteScopeRepository(directory), comparison_html, jobs)
