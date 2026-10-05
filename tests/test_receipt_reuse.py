"""Continuation preserves independent passes and records reuse without new spend."""
from dataclasses import asdict, replace
from decimal import Decimal
import pytest

from independent_judge.domain.evaluation import JudgeConfig, Prompt, LlmResult, EvaluationError
from independent_judge.infrastructure.run_repository import RunRepository
from independent_judge.infrastructure.receipt_reuse import ReceiptReuseJudge


class Live:
    def __init__(self): self.calls = []
    def complete(self, prompt, config):
        self.calls.append(prompt)
        return LlmResult('live', config.model, {}, Decimal('.01'), {})


def saved(tmp_path):
    repository = RunRepository(tmp_path)
    config = JudgeConfig()
    prompt = Prompt('s', 'u', 'v1')
    repository.begin('old', {'config': asdict(config)})
    for index in range(3):
        raw = {'model': config.model, 'usage': {'prompt_tokens': 5, 'completion_tokens': 5, 'cost': .01},
               'choices': [{'finish_reason': 'stop', 'message': {'content': str(index)}}]}
        repository.receipt('old', str(index), {'prompt': asdict(prompt), 'raw': raw,
            'started_at': f'2026-01-01T00:00:0{index}Z', 'cost_usd': '.01'})
    repository.finish('old', {'id': 'old', 'status': 'failed'})
    return repository, config, prompt


def test_identical_prompt_passes_reuse_distinct_receipts_in_order(tmp_path):
    repository, config, prompt = saved(tmp_path)
    live = Live()
    judge = ReceiptReuseJudge(live, repository.path, 'old', config)
    for index in range(3):
        result = judge.complete(prompt, config)
        assert result.text == str(index)
        assert result.cost_usd == 0
        assert result.usage['completion_tokens'] == 0
        assert result.raw['reused_from']['call_id'] == str(index)
        assert result.raw['original_response']['usage']['cost'] == .01
    assert live.calls == []
    assert judge.complete(prompt, config).text == 'live'
    assert len(live.calls) == 1


def test_changed_prompt_or_configuration_never_reuses(tmp_path):
    repository, config, prompt = saved(tmp_path)
    live = Live()
    judge = ReceiptReuseJudge(live, repository.path, 'old', config)
    assert judge.complete(replace(prompt, version='v2'), config).text == 'live'
    with pytest.raises(EvaluationError):
        ReceiptReuseJudge(live, repository.path, 'old', replace(config, max_tokens=8192))


def test_missing_source_run_cannot_silently_start_fresh(tmp_path):
    repository, config, _ = saved(tmp_path)
    with pytest.raises(EvaluationError):
        ReceiptReuseJudge(Live(), repository.path, 'missing', config)
