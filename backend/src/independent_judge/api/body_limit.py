"""Bound the real request body before multipart or JSON parsing."""
from collections import deque

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from independent_judge.domain.inputs import MAX_FILE_BYTES

MAX_REQUEST_BYTES = 3 * MAX_FILE_BYTES + 1024 * 1024


class RequestBodyLimit:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        chunks = deque()
        received = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            received += len(message.get("body", b""))
            if received > MAX_REQUEST_BYTES:
                await JSONResponse(status_code=413, content={"error": {
                    "code": "request_too_large", "message": "Total request exceeds 61 MiB. Each file is limited to 20 MiB.",
                }})(scope, receive, send)
                return
            chunks.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            return chunks.popleft() if chunks else await receive()

        await self.app(scope, replay, send)
