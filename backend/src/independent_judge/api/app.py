"""Compose local comparisons; live provider requires explicit operator settings."""
from pathlib import Path
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI

from independent_judge.api.errors import input_error_handler
from independent_judge.api.body_limit import RequestBodyLimit
from independent_judge.api.inputs import build_router
from independent_judge.bootstrap import build_intake, build_scope, build_editorial, build_comparison_view
from independent_judge.api.comparison_view import build_comparison_router
from independent_judge.api.scope import build_scope_router
from independent_judge.api.editorial_review import build_editorial_router
from independent_judge.api.local_access import LocalStandAccess
from independent_judge.domain.errors import InputError
from independent_judge.bootstrap import data_directory
from independent_judge.application.local_evaluation import LocalEvaluation
from independent_judge.infrastructure.local_jobs import LocalJobs
from independent_judge.infrastructure.hadith_library import HadithLibrary
from independent_judge.infrastructure.scope_repository import SqliteScopeRepository
from independent_judge.api.local_runs import build_run_router
from independent_judge.infrastructure.sunnah_source import SunnahSource


def create_app(data_dir: Path | None = None, *, evaluation=None) -> FastAPI:
    from independent_judge.runtime_evaluation import configured_evaluation
    directory = data_directory(data_dir)
    jobs = LocalJobs(directory)
    runner = LocalEvaluation(SqliteScopeRepository(directory), jobs, HadithLibrary(directory),
                             evaluation or configured_evaluation(directory),
                             SunnahSource(os.environ['SUNNAH_API_KEY']) if os.environ.get('SUNNAH_API_KEY') else None)
    view = build_comparison_view(directory, jobs)

    @asynccontextmanager
    async def lifespan(app):
        runner.start()
        try: yield
        finally: runner.close()

    app = FastAPI(title="Independent Judge", version="0.1.0",
                  lifespan=lifespan, description="Local translation comparisons. Live calls require explicit operator configuration.")
    app.add_exception_handler(InputError, input_error_handler)
    app.add_middleware(RequestBodyLimit)
    app.add_middleware(LocalStandAccess)
    app.include_router(build_router(build_intake(data_dir)))
    app.include_router(build_scope_router(build_scope(data_dir)))
    app.state.editorial=build_editorial(data_dir)
    app.include_router(build_editorial_router(app.state.editorial))
    app.include_router(build_comparison_router(view))
    app.include_router(build_run_router(runner, view))

    @app.get("/health")
    def health():
        return {"status": "ok", "stage": "comparison", "live_enabled": runner.runtime is not None}

    return app
