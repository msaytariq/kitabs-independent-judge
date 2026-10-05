"""Gemini routing, explicit configuration and shared dollar admission boundaries."""
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

import httpx
import pytest

from independent_judge.domain.budget import reservation
from independent_judge.domain.evaluation import EvaluationError, JudgeConfig, Prompt
from independent_judge.infrastructure.gateway import GatewayJudge
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository
from independent_judge.application.run_admission import AdmittedCalls


def gemini():
    return JudgeConfig(model='google/gemini-3.8-flash', provider='google',
        max_tokens=8192, reasoning_effort='high', input_usd_per_million='0.75',
        output_usd_per_million='3.75', reserve_input_usd_per_million='0.825',
        price_version='vercel-google-2026-10-05')


def test_gemini_wire_schema_and_reported_thinking_cost():
    schema = {'type': 'object', 'properties': {}, 'additionalProperties': False}
    def handler(request):
        body = json.loads(request.content)
        assert body['model'] == 'google/gemini-3.8-flash'
        assert body['providerOptions'] == {'gateway': {'only': ['google']}}
        assert body['reasoning'] == {'effort': 'high'}
        assert body['max_tokens'] == 8192
        assert body['response_format']['json_schema'] == {
            'name': 'test_v1', 'strict': True, 'schema': schema}
        assert 'temperature' not in body and 'top_p' not in body
        return httpx.Response(200, json={'model': body['model'],
            'choices': [{'finish_reason': 'stop', 'message': {'content': '{}'}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 800,
                'completion_tokens_details': {'reasoning_tokens': 700}, 'cost': '0.003075'}})
    result = GatewayJudge('test', transport=httpx.MockTransport(handler)).complete(
        Prompt('policy', 'data', 'test-v1', schema), gemini())
    assert result.cost_usd == Decimal('0.003075')
    assert result.usage['completion_tokens_details']['reasoning_tokens'] == 700


@pytest.mark.parametrize('change,code', [
    ({'provider': 'vertex'}, 'unreviewed_model'),
    ({'output_usd_per_million': '0'}, 'unreviewed_price'),
    ({'reasoning_effort': 'medium'}, 'unreviewed_reasoning'),
    ({'max_tokens': 32000}, 'pilot_bounds'),
    ({'max_tokens': True}, 'pilot_bounds'),
])
def test_unreviewed_gemini_configuration_never_reaches_gateway(change, code):
    requests = []
    judge = GatewayJudge('test', transport=httpx.MockTransport(lambda r: requests.append(r)))
    with pytest.raises(EvaluationError) as error:
        judge.complete(Prompt('p', 'u', 'v1'), replace(gemini(), **change))
    assert error.value.code == code
    assert requests == []


def test_gemini_admission_respects_prior_translation_spend(tmp_path):
    ledger = BudgetLedger(tmp_path, total_usd=Decimal('1'), per_run_usd=Decimal('1'))
    ledger.reserve('translation', 'b', Decimal('0.98'))
    ledger.settle('translation', 'b', Decimal('0.98'))
    prompt = Prompt('p', 'u', 'v1')
    assert Decimal('0.04') < reservation(prompt, gemini()) < Decimal('0.05')
    requests = []
    calls = AdmittedCalls(GatewayJudge('test', transport=httpx.MockTransport(
        lambda r: requests.append(r))), ledger, RunRepository(tmp_path), 'judge', gemini())
    with pytest.raises(EvaluationError):
        calls('assessment', prompt)
    assert requests == []
    assert ledger.summary()['committed_usd'] == '0.980000'


def test_reviewed_file_loads_and_partial_settings_fail(tmp_path):
    from independent_judge.operator_config import load_judge_config
    path = Path(__file__).resolve().parents[1] / 'config/judge-gemini-3.8-flash.json'
    assert load_judge_config(path) == replace(gemini(), reasoning_effort='low')
    invalid = tmp_path / 'partial.json'
    invalid.write_text('{"model":"google/gemini-3.8-flash"}')
    with pytest.raises(ValueError, match='all judge configuration fields'):
        load_judge_config(invalid)


def test_http_runtime_uses_explicit_gemini_config_without_spending(tmp_path, monkeypatch):
    from independent_judge import runtime_evaluation
    config_path = Path(__file__).resolve().parents[1] / 'config/judge-gemini-3.8-flash.json'
    monkeypatch.setenv('JUDGE_ENABLE_LIVE', '1')
    monkeypatch.setenv('JUDGE_CONFIG_PATH', str(config_path))
    monkeypatch.setenv('JUDGE_BUDGET_TOTAL_USD', '1')
    monkeypatch.setenv('JUDGE_BUDGET_RUN_USD', '1')
    monkeypatch.setenv('AI_GATEWAY_API_KEY', 'offline-test')
    monkeypatch.setattr(runtime_evaluation, 'code_checkpoint', lambda _: 'a' * 40)
    runtime = runtime_evaluation.configured_evaluation(tmp_path)
    assert runtime.config == replace(gemini(), reasoning_effort='low')
    assert runtime.budget.summary()['calls'] == 0


def test_cli_defaults_to_gemini_preflight_without_spending(tmp_path, monkeypatch, capsys):
    from fastapi.testclient import TestClient
    from independent_judge.api.app import create_app
    from independent_judge.cli import main
    from test_local_runs import prepare
    monkeypatch.delenv('JUDGE_CONFIG_PATH', raising=False)
    monkeypatch.delenv('JUDGE_ENABLE_LIVE', raising=False)
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    with TestClient(create_app(tmp_path)) as client:
        scope = prepare(client)
    monkeypatch.setattr('sys.argv', ['judge', '--data-dir', str(tmp_path),
        '--scope-id', scope, '--run-id', 'preflight'])
    main()
    assert json.loads(capsys.readouterr().out)['model'] == gemini().model
    assert not (tmp_path / 'budget.sqlite3').exists()
