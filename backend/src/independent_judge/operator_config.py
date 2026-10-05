"""Load the same explicit, reviewed judge configuration for HTTP and CLI runs."""
from dataclasses import fields
import json
from pathlib import Path

from independent_judge.domain.evaluation import JudgeConfig
from independent_judge.domain.reviewed_models import validate_config


def load_judge_config(path: Path) -> JudgeConfig:
    settings = json.loads(path.read_text(encoding='utf-8'))
    expected = {field.name for field in fields(JudgeConfig)}
    if not isinstance(settings, dict) or set(settings) not in (expected, expected - {'temperature'}):
        raise ValueError('Specify all judge configuration fields explicitly')
    config = JudgeConfig(**settings)
    validate_config(config)
    return config
