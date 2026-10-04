"""Central error translation. Client responses never expose exception traces."""
from fastapi import Request
from fastapi.responses import JSONResponse

from independent_judge.domain.errors import InputError


async def input_error_handler(request: Request, exc: InputError) -> JSONResponse:
    status = {"file_too_large": 413, "request_too_large": 413,
              "unsupported_format": 415, "comparison_not_found": 404}.get(exc.code, 422)
    return JSONResponse(status_code=status, content={"error": {"code": exc.code, "message": str(exc)}})
