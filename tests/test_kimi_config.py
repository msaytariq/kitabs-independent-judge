from dataclasses import replace
from pathlib import Path
from decimal import Decimal
import pytest
from independent_judge.domain.evaluation import EvaluationError, Prompt
from independent_judge.operator_config import load_judge_config
from independent_judge.infrastructure.gateway import payload
from independent_judge.domain.budget import reservation


def config():
    return load_judge_config(Path(__file__).parents[1] / 'config/judge-kimi-k3.json')


def test_kimi_preserves_requested_settings_and_records_unsupported_temperature():
    settings = config()
    assert settings.temperature == 0
    wire = payload(Prompt('instructions', 'text', 'test'), settings)
    assert wire['model'] == 'moonshotai/kimi-k3'
    assert wire['max_tokens'] == 32000
    assert wire['reasoning'] == {'effort': 'none'}
    assert 'temperature' not in wire  # Catalog explicitly excludes temperature.
    assert wire['providerOptions']['gateway']['only'] == ['moonshotai']
    assert Decimal('.6') < reservation(Prompt('', '', 'test'), settings) < Decimal('.7')


def test_kimi_rejects_changed_prices_and_oversized_output():
    for changes in ({'max_tokens': 32001}, {'output_usd_per_million': '0'}, {'temperature': 1}):
        with pytest.raises(EvaluationError):
            payload(Prompt('', '', 'test'), replace(config(), **changes))
