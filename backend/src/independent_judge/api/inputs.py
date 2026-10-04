"""Draft intake and preview routes; no evaluation is triggered here."""
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool

from independent_judge.application.intake import IntakeService, Upload
from independent_judge.api.schemas import ComparisonView, TextInputs
from independent_judge.api.uploads import read_upload


def build_router(intake: IntakeService) -> APIRouter:
    router = APIRouter(prefix="/api/comparisons", tags=["intake"])

    @router.post("", status_code=201, response_model=ComparisonView)
    async def upload_files(source: Annotated[UploadFile, File()], a: Annotated[UploadFile, File()],
                           b: Annotated[UploadFile, File()], source_language: Annotated[str, Form()],
                           target_language: Annotated[str, Form()]):
        uploads = [await read_upload(file) for file in (source, a, b)]
        comparison = await run_in_threadpool(intake.create, *uploads, source_language, target_language)
        return ComparisonView.from_comparison(comparison)

    @router.post("/text", status_code=201, response_model=ComparisonView)
    def paste_text(inputs: TextInputs):
        uploads = [Upload(getattr(inputs, role).encode("utf-8"), f"{role}.txt", "text/plain")
                   for role in ("source", "a", "b")]
        return ComparisonView.from_comparison(intake.create(*uploads, inputs.source_language, inputs.target_language))

    @router.get("/{comparison_id}", response_model=ComparisonView)
    def preview(comparison_id: str):
        return ComparisonView.from_comparison(intake.get(comparison_id))

    return router
