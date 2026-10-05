"""Every platform HTTP attempt must fit the shared ledger before transmission."""
import asyncio
from decimal import Decimal
import json

import httpx
import pytest

from independent_judge.domain.evaluation import EvaluationError
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.platform_budget_transport import BudgetedGatewayTransport


RATES = {'test/model': {'provider': 'test', 'input': '0.00000375', 'output': '0.000015'}}
BODY = {'model': 'test/model', 'messages': [{'role': 'user', 'content': 'hello'}],
        'max_tokens': 32000, 'stream': True, 'stream_options': {'include_usage': True}}


class Frames(httpx.AsyncByteStream):
    def __init__(self, pieces): self.pieces = pieces
    async def __aiter__(self):
        for piece in self.pieces: yield piece


def receipt(cost='0.1'):
    return ('data: ' + json.dumps({'model': 'test/model', 'usage': {
        'prompt_tokens': 100, 'completion_tokens': 100, 'cost': cost}}) + '\n\ndata: [DONE]\n\n').encode()


def ledger(path):
    return BudgetLedger(path, total_usd=Decimal('1'), per_run_usd=Decimal('1'))


def test_stream_fragments_settle_once_and_preserve_payload(tmp_path):
    budget = ledger(tmp_path)
    wire = receipt()
    def handler(request):
        body = json.loads(request.content)
        assert body['messages'] == BODY['messages']
        assert body['max_tokens'] == 32000
        assert body['providerOptions']['gateway'] == {'only': ['test']}
        return httpx.Response(200, stream=Frames([wire[:17], wire[17:73], wire[73:]]))
    async def run():
        transport = BudgetedGatewayTransport(budget, tmp_path, 'b', RATES,
            inner_factory=lambda: httpx.MockTransport(handler))
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.post('https://ai-gateway.vercel.sh/v1/chat/completions', json=BODY)
            assert response.content == wire
    asyncio.run(run())
    assert budget.summary()['reported_usd'] == '0.100000'
    assert budget.summary()['unresolved_reserved_usd'] == '0.000000'
    assert len(list((tmp_path / 'platform-receipts').glob('*.sse'))) == 1


def test_unknown_attempt_stays_reserved_and_retry_cannot_escape_total(tmp_path):
    budget = ledger(tmp_path)
    requests = []
    def handler(request):
        requests.append(request)
        raise httpx.ReadError('wire broke')
    async def run():
        transport = BudgetedGatewayTransport(budget, tmp_path, 'b', RATES,
            inner_factory=lambda: httpx.MockTransport(handler))
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(httpx.ReadError):
                await client.post('https://ai-gateway.vercel.sh/v1/chat/completions', json=BODY)
            with pytest.raises(EvaluationError) as error:
                await client.post('https://ai-gateway.vercel.sh/v1/chat/completions', json=BODY)
            assert error.value.code == 'budget_exceeded'
    asyncio.run(run())
    assert len(requests) == 1
    assert Decimal(budget.summary()['unresolved_reserved_usd']) > Decimal('0.6')


@pytest.mark.parametrize('body', [BODY | {'tools': [{}]}, BODY | {'model': 'unknown'},
    BODY | {'max_tokens': None}, BODY | {'service_tier': 'priority'},
    BODY | {'messages': [{'role': 'user', 'content': [{'type': 'image_url'}]}]}])
def test_unpriced_options_never_leave_process(tmp_path, body):
    requests = []
    async def run():
        transport = BudgetedGatewayTransport(ledger(tmp_path), tmp_path, 'b', RATES,
            inner_factory=lambda: httpx.MockTransport(lambda r: requests.append(r)))
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(EvaluationError):
                await client.post('https://ai-gateway.vercel.sh/v1/chat/completions', json=body)
    asyncio.run(run())
    assert requests == []


@pytest.mark.parametrize('wire', [b'data: [DONE]\n\n', receipt().replace(b'data: [DONE]\n\n', b'')])
def test_unpriced_or_incomplete_stream_cannot_be_success(tmp_path, wire):
    budget = ledger(tmp_path)
    async def run():
        transport = BudgetedGatewayTransport(budget, tmp_path, 'b', RATES,
            inner_factory=lambda: httpx.MockTransport(lambda _: httpx.Response(200, stream=Frames([wire]))))
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(EvaluationError):
                await client.post('https://ai-gateway.vercel.sh/v1/chat/completions', json=BODY)
    asyncio.run(run())
    assert Decimal(budget.summary()['unresolved_reserved_usd']) > 0
