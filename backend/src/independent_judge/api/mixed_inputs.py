"""Multipart input parity without coupling format extraction to routes."""
from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool
from independent_judge.api.schemas import ComparisonView
from independent_judge.api.uploads import read_upload


def build_mixed_router(service):
    router = APIRouter(prefix='/api/comparisons', tags=['intake'])

    @router.post('/mixed', status_code=201, response_model=ComparisonView)
    async def mixed(
        source_kind: Annotated[str, Form()], a_kind: Annotated[str, Form()], b_kind: Annotated[str, Form()],
        source_language: Annotated[str, Form()], target_language: Annotated[str, Form()],
        source_value: Annotated[str, Form()] = '', a_value: Annotated[str, Form()] = '', b_value: Annotated[str, Form()] = '',
        source: Annotated[UploadFile | None, File()] = None,
        a: Annotated[UploadFile | None, File()] = None, b: Annotated[UploadFile | None, File()] = None,
    ):
        entries = dict(zip(('source', 'a', 'b'), [
            {'kind': kind, 'value': value} for kind, value in zip(
                (source_kind, a_kind, b_kind), (source_value, a_value, b_value))]))
        files = {role: await read_upload(file) for role, file in zip(('source','a','b'), (source,a,b)) if file}
        result = await run_in_threadpool(service.create, entries, files, source_language, target_language)
        return ComparisonView.from_comparison(result)

    return router
