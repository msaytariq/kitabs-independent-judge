"""Budget every HTTP attempt of the unmodified platform Gateway adapter."""
import json
from uuid import uuid4
import httpx

from independent_judge.domain.evaluation import EvaluationError
from independent_judge.domain.platform_request_budget import bounded_request
from independent_judge.infrastructure.platform_usage_stream import UsageStream


class BudgetedGatewayTransport(httpx.AsyncBaseTransport):
    def __init__(self, ledger, directory, run_id, rates, *, inner_factory=None, on_progress=None):
        self.ledger, self.run_id, self.rates = ledger, run_id, rates
        self.directory = directory / 'platform-receipts'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.inner_factory = inner_factory or (lambda: httpx.AsyncHTTPTransport(retries=0))
        self.on_progress = on_progress

    async def handle_async_request(self, request):
        if request.method != 'POST' or str(request.url) != 'https://ai-gateway.vercel.sh/v1/chat/completions':
            raise EvaluationError('unreviewed_endpoint', 'Only the Gateway completion endpoint is admitted.')
        data, reserve = bounded_request(json.loads(await request.aread()), self.rates)
        call_id = uuid4().hex
        self.ledger.reserve(self.run_id, call_id, reserve)
        (self.directory / (call_id + '.request.json')).write_bytes(data)
        if self.on_progress: self.on_progress(call_id, 'reserved', self.ledger.summary())
        headers = dict(request.headers)
        headers['content-length'] = str(len(data))
        guarded = httpx.Request(request.method, request.url, headers=headers,
                                content=data, extensions=request.extensions)
        inner = self.inner_factory()
        try:
            response = await inner.handle_async_request(guarded)
        except BaseException:
            await inner.aclose()
            raise
        if response.status_code != 200:
            await response.aclose()
            await inner.aclose()
            raise EvaluationError('gateway_http', f'Gateway returned HTTP {response.status_code}; reservation remains held.')
        return httpx.Response(200, headers=response.headers, extensions=response.extensions,
            stream=UsageStream(response.stream, inner, self.ledger, self.run_id, call_id,
                               self.directory / (call_id + '.sse'), self.on_progress))
