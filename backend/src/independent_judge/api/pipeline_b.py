"""Local embedded pipeline launch and polling; credentials never reach the browser."""
from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
from independent_judge.api.uploads import read_upload
from independent_judge.application.intake import Upload
from independent_judge.domain.errors import InputError


def build_pipeline_router(service, retriever):
    router = APIRouter(prefix='/api/pipeline-b', tags=['pipeline-b'])

    @router.get('/capabilities')
    def capabilities():
        return {'enabled': service.available(), 'remaining': service.remaining()}

    @router.post('', status_code=202)
    async def submit(request_id: Annotated[str, Form()], source_kind: Annotated[str, Form()],
                     source_language: Annotated[str, Form()], target_language: Annotated[str, Form()],
                     source_value: Annotated[str, Form()] = '', source: Annotated[UploadFile | None, File()] = None):
        if source_kind == 'file' and source:
            upload = await read_upload(source)
        elif source_kind == 'text':
            # A browser sends form line breaks as CRLF; the comparison keeps the LF of the screen.
            upload = Upload(source_value.replace('\r\n', '\n').encode(), 'source.txt', 'text/plain')
        elif source_kind == 'url':
            remote = await run_in_threadpool(retriever.fetch, source_value)
            upload = Upload(remote.content, remote.filename, remote.content_type, remote.provenance)
        else:
            raise InputError('missing_input', 'Provide a source text or file.')
        return await run_in_threadpool(service.submit, request_id, upload, source_language, target_language)

    @router.get('/{request_id}')
    def status(request_id: str):
        return service.status(request_id)

    @router.get('/{request_id}/typeset.pdf')
    def typeset(request_id: str):
        content = service.typeset_file(request_id)
        return Response(content, media_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="kitabs-b-typeset.pdf"'})

    return router
