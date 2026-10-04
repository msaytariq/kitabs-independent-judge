"""Bounded upload reads; extraction belongs to the intake service."""
from fastapi import UploadFile

from independent_judge.application.intake import Upload
from independent_judge.domain.errors import InputError
from independent_judge.domain.inputs import MAX_FILE_BYTES


async def read_upload(file: UploadFile) -> Upload:
    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise InputError("file_too_large", "Each file must be at most 20 MiB.")
    return Upload(content, file.filename or "", file.content_type or "application/octet-stream")
