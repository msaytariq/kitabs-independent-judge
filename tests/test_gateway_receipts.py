"""Live-pilot regressions, using invented text and real receipt field structure."""
import json
from decimal import Decimal
import pytest
import httpx
from independent_judge.domain.evaluation import JudgeConfig,EvaluationError
from independent_judge.domain.judge_prompt import assessment_prompt
from independent_judge.domain.judge_parsing import parse_findings
from independent_judge.domain.critical_review_prompt import critical_prompt
from independent_judge.domain.cross_check_prompt import cross_prompt
from independent_judge.domain.completeness import inventory_prompt,coverage_prompt
from independent_judge.infrastructure.gateway import GatewayJudge,reported_cost,payload
from independent_judge.infrastructure.budget_repository import BudgetLedger
from test_judge_contracts import sample


def receipt(finish='stop'):
    return {'model':JudgeConfig().model,'choices':[{'finish_reason':finish,'message':{'content':'{"findings":[]}'}}],
            'usage':{'prompt_tokens':1648,'completion_tokens':1287,'cost':.016166,
                     'surcharge_cost':.0001,'gateway_cost':.016266,'provider_allowlist_cost':.0001}}


def test_schema_prevents_missing_severity_at_generation_boundary():
    response=payload(assessment_prompt(sample(),'a'),JudgeConfig())['response_format']
    assert response['type']=='json_schema' and response['json_schema']['strict'] is True
    schema=response['json_schema']['schema']
    assert 'code' in schema['properties']['findings']['items']['required']
    assert schema['properties']['findings']['items']['properties']['code']['enum']==['K','T','A','S']
    # Existing bad receipts remain invalid. No code is guessed or backfilled.
    with pytest.raises(EvaluationError):
        parse_findings('{"findings":[{"source_excerpt":"x","current_text":"y","should_be":"z","why":"x","repeated":false}]}','x','y')


def test_all_stages_have_required_structured_response_contracts():
    s=sample()
    for prompt in (assessment_prompt(s,'a'),critical_prompt(s,'a',[]),cross_prompt(s,'a',[]),inventory_prompt(s),coverage_prompt(s,'a',[])):
        schema=payload(prompt,JudgeConfig())['response_format']['json_schema']['schema']
        assert schema['type']=='object' and schema['additionalProperties'] is False
        assert set(schema['required'])==set(schema['properties'])


def test_gateway_total_includes_surcharge_without_double_counting():
    g=GatewayJudge('test',transport=httpx.MockTransport(lambda _:httpx.Response(200,json=receipt())))
    result=g.complete(assessment_prompt(sample(),'a'),JudgeConfig())
    assert result.cost_usd==Decimal('.016266')
    assert reported_cost({'usage':{'cost':.01,'surcharge_cost':.0001}})==Decimal('.0101')
    assert reported_cost({'usage':{'cost':.01,'gateway_cost':'bad'}}) is None
    assert reported_cost({'usage':{'cost':.01,'gateway_cost':-.1}}) is None


def test_priced_truncated_response_exposes_total_cost_to_application():
    g=GatewayJudge('test',transport=httpx.MockTransport(lambda _:httpx.Response(200,json=receipt('length'))))
    with pytest.raises(EvaluationError) as exc:g.complete(assessment_prompt(sample(),'a'),JudgeConfig())
    assert exc.value.cost_usd==Decimal('.016266')


def test_reconciliation_is_append_only_and_enforced_on_future_admission(tmp_path):
    ledger=BudgetLedger(tmp_path,total_usd=Decimal('3'),per_run_usd=Decimal('1'))
    ledger.reserve('r','call',Decimal('.03'));ledger.settle('r','call',Decimal('.016166'))
    ledger.reconcile('r','call',Decimal('.016266'),'a'*64)
    ledger.reconcile('r','call',Decimal('.016266'),'a'*64)
    assert ledger.summary()['reported_usd']=='0.016266'
    with ledger.connect() as db:
        assert db.execute('SELECT actual FROM calls').fetchone()[0]==16166
    with pytest.raises(EvaluationError):ledger.reserve('r','next',Decimal('.9838'))
    with pytest.raises(EvaluationError):ledger.reconcile('r','call',Decimal('.015'),'a'*64)
