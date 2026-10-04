"""Budget survives restarts, concurrent admissions, invalid provider responses."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
import httpx
import pytest
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.gateway import GatewayJudge
from independent_judge.domain.evaluation import JudgeConfig, Prompt, EvaluationError


def test_atomic_duplicate_admission_and_persistent_limits(tmp_path):
    ledger = BudgetLedger(tmp_path, total_usd=Decimal('3'), per_run_usd=Decimal('1'))
    def claim(_):
        try:
            ledger.reserve('run','call',Decimal('0.6')); return True
        except EvaluationError:
            return False
    with ThreadPoolExecutor(4) as pool:
        assert sum(pool.map(claim,range(4))) == 1
    restarted = BudgetLedger(tmp_path,total_usd=Decimal('3'),per_run_usd=Decimal('1'))
    with pytest.raises(EvaluationError): restarted.reserve('run','second',Decimal('0.5'))
    restarted.settle('run','call',Decimal('0.1'))
    restarted.reserve('run','second',Decimal('0.5'))
    assert restarted.summary()['committed_usd'] == '0.600000'
    with pytest.raises(EvaluationError): BudgetLedger(tmp_path,total_usd=Decimal('30'),per_run_usd=Decimal('10'))


def test_total_cap_and_no_unbounded_mode(tmp_path):
    with pytest.raises(EvaluationError): BudgetLedger(tmp_path,total_usd=Decimal('0'),per_run_usd=Decimal('1'))
    l=BudgetLedger(tmp_path,total_usd=Decimal('3'),per_run_usd=Decimal('1'))
    for i in range(3): l.reserve(str(i),'call',Decimal('1'))
    with pytest.raises(EvaluationError): l.reserve('fourth','call',Decimal('0.001'))
    with pytest.raises(EvaluationError): l.reserve('fifth','call',Decimal('-1'))


def response(**changes):
    return {'id':'gen-test','model':'anthropic/claude-sonnet-5.5',
            'choices':[{'finish_reason':'stop','message':{'content':'{"findings":[]}'}}],
            'usage':{'prompt_tokens':123,'completion_tokens':55,'cost':0.001}} | changes


def test_gateway_wire_omits_sampling_pins_provider_and_records_actual_cost():
    def handler(request):
        body=json.loads(request.content)
        assert str(request.url)=='https://ai-gateway.vercel.sh/v1/chat/completions'
        assert 'temperature' not in body and 'top_p' not in body
        assert body['providerOptions']['gateway']['only']==['anthropic']
        assert body['reasoning']['effort']=='medium'
        assert body['max_tokens']==4096
        return httpx.Response(200,json=response())
    g=GatewayJudge('test',transport=httpx.MockTransport(handler))
    r=g.complete(Prompt('policy','data','test-v1'),JudgeConfig())
    assert r.cost_usd==Decimal('0.001') and r.actual_model==JudgeConfig().model
    assert r.usage['completion_tokens']==55


@pytest.mark.parametrize('changes,code', [
    ({'choices':[{'finish_reason':'length','message':{'content':'partial'}}]},'truncated'),
    ({'usage':{}},'missing_usage'),
    ({'model':'other/model'},'model_mismatch'),
])
def test_provider_failure_is_explicit(changes,code):
    g=GatewayJudge('test',transport=httpx.MockTransport(lambda _:httpx.Response(200,json=response(**changes))))
    with pytest.raises(EvaluationError) as exc: g.complete(Prompt('policy','data','test-v1'),JudgeConfig())
    assert exc.value.code==code
    assert exc.value.raw is not None


def test_http_error_has_no_retry_or_secret_echo():
    calls=[]
    def handler(r):
        calls.append(r); return httpx.Response(401,json={'error':'secret-like response'})
    with pytest.raises(EvaluationError) as exc:
        GatewayJudge('private-token',transport=httpx.MockTransport(handler)).complete(Prompt('p','u','v1'),JudgeConfig())
    assert len(calls)==1
    assert 'private-token' not in str(exc.value)
