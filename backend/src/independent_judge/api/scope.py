"""Typed manual selections and stored previews; no alignment guesses."""
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, StrictInt, StrictBool
from independent_judge.application.prepare_scope import ScopeService
from independent_judge.domain.scope import TextRange


class RangeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start: StrictInt
    end: StrictInt
    text_sha256: str


class RangesRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source: RangeRequest
    a: RangeRequest
    b: RangeRequest


class ScopeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ranges: RangesRequest
    profile: str = 'general'
    confirmed: StrictBool = False
    pipeline_request_id: str | None = None


def build_scope_router(service: ScopeService) -> APIRouter:
    router = APIRouter()

    @router.post('/api/comparisons/{comparison_id}/scopes', status_code=201)
    def prepare(comparison_id: str, request: ScopeRequest):
        return service.create(comparison_id, {k: TextRange(**v) for k, v in request.ranges.model_dump().items()},
                              request.profile, request.confirmed, pipeline_request_id=request.pipeline_request_id)

    @router.get('/api/scopes/{scope_id}')
    def preview(scope_id: str):
        return service.get(scope_id)

    return router
