"""Compose the local intake and editorial workbench; no provider is configured."""
from pathlib import Path
from fastapi import FastAPI

from independent_judge.api.errors import input_error_handler
from independent_judge.api.body_limit import RequestBodyLimit
from independent_judge.api.inputs import build_router
from independent_judge.bootstrap import build_intake, build_scope, build_editorial
from independent_judge.api.scope import build_scope_router
from independent_judge.api.editorial_review import build_editorial_router
from independent_judge.api.local_access import LocalStandAccess
from independent_judge.domain.errors import InputError


def create_app(data_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Independent Judge", version="0.1.0",
                  description="Local intake and editorial workbench. Public session access is not implemented.")
    app.add_exception_handler(InputError, input_error_handler)
    app.add_middleware(RequestBodyLimit)
    app.add_middleware(LocalStandAccess)
    app.include_router(build_router(build_intake(data_dir)))
    app.include_router(build_scope_router(build_scope(data_dir)))
    app.state.editorial=build_editorial(data_dir)
    app.include_router(build_editorial_router(app.state.editorial))

    @app.get("/health")
    def health():
        return {"status": "ok", "stage": "editorial-workbench", "live_enabled": False}

    return app
