"""Local embedded pipeline launch and polling; credentials never reach the browser."""
from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool
from independent_judge.api.uploads import read_upload
from independent_judge.application.intake import Upload
from independent_judge.domain.errors import InputError


def build_pipeline_router(service, retriever):
    router = APIRouter(prefix='/api/pipeline-b', tags=['pipeline-b'])

    @router.get('/capabilities')
    def capabilities():
        return {'enabled': service.platform is not None}

    @router.post('', status_code=202)
    async def submit(request_id: Annotated[str, Form()], source_kind: Annotated[str, Form()],
                     source_language: Annotated[str, Form()], target_language: Annotated[str, Form()],
                     source_value: Annotated[str, Form()] = '', source: Annotated[UploadFile | None, File()] = None):
        if source_kind == 'file' and source:
            upload = await read_upload(source)
        elif source_kind == 'text':
            upload = Upload(source_value.encode(), 'source.txt', 'text/plain')
        elif source_kind == 'url':
            remote = await run_in_threadpool(retriever.fetch, source_value)
            upload = Upload(remote.content, remote.filename, remote.content_type, remote.provenance)
        else:
            raise InputError('missing_input', 'Provide a source text or file.')
        return await run_in_threadpool(service.submit, request_id, upload, source_language, target_language)

    @router.get('/{request_id}')
    def status(request_id: str):
        return service.status(request_id)

    return router
