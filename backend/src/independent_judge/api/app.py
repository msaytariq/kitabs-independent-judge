"""Local-only intake application factory; no evaluation provider is configured."""
from pathlib import Path
from fastapi import FastAPI

from independent_judge.api.errors import input_error_handler
from independent_judge.api.body_limit import RequestBodyLimit
from independent_judge.api.inputs import build_router
from independent_judge.bootstrap import build_intake
from independent_judge.domain.errors import InputError


def create_app(data_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Independent Judge", version="0.1.0",
                  description="Local intake milestone. Do not expose publicly before session access is implemented.")
    app.add_exception_handler(InputError, input_error_handler)
    app.add_middleware(RequestBodyLimit)
    app.include_router(build_router(build_intake(data_dir)))

    @app.get("/health")
    def health():
        return {"status": "ok", "stage": "intake", "live_enabled": False}

    return app
