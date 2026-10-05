"""The second judge comes from a family that made neither translation nor the first assessment."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import pytest
from independent_judge.domain.budget import reservation
from independent_judge.domain.evaluation import EvaluationError, Prompt
from independent_judge.infrastructure.gateway import payload
from independent_judge.operator_config import load_judge_config


def config():
    return load_judge_config(Path(__file__).parents[1] / 'config/judge-grok-4.1-fast.json')


def test_grok_route_uses_the_reviewed_gateway_provider_and_prices():
    settings = config()
    wire = payload(Prompt('instructions', 'text', 'test'), settings)
    assert wire['model'] == 'spacexai/grok-4.1-fast-reasoning'
    assert wire['providerOptions']['gateway']['only'] == ['vertex']
    assert wire['reasoning'] == {'effort': 'low'} and wire['max_tokens'] == 8192
    assert Decimal('0') < reservation(Prompt('', '', 'test'), settings) < Decimal('.01')


def test_grok_rejects_changed_prices_and_unreviewed_effort():
    for changes in ({'output_usd_per_million': '0.4'}, {'reasoning_effort': 'high'}, {'max_tokens': 8193}):
        with pytest.raises(EvaluationError):
            payload(Prompt('', '', 'test'), replace(config(), **changes))
