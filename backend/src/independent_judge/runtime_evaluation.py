"""Explicit operator configuration, isolated from platform settings and secrets."""
from dataclasses import fields
from decimal import Decimal
import json
import os
from pathlib import Path
from independent_judge.application.local_evaluation import EvaluationRuntime
from independent_judge.domain.evaluation import JudgeConfig
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository
from independent_judge.infrastructure.gateway import GatewayJudge, payload
from independent_judge.domain.evaluation import Prompt
from independent_judge.cli import code_checkpoint


def configured_evaluation(directory: Path) -> EvaluationRuntime | None:
    if os.environ.get('JUDGE_ENABLE_LIVE') != '1': return None
    config_path = os.environ.get('JUDGE_CONFIG_PATH')
    if not config_path: raise ValueError('JUDGE_CONFIG_PATH is required for live evaluation')
    settings = json.loads(Path(config_path).read_text())
    expected = {f.name for f in fields(JudgeConfig)}
    if set(settings) != expected: raise ValueError('Specify all judge configuration fields explicitly')
    config = JudgeConfig(**settings)
    payload(Prompt('', '', 'preflight'), config)  # Validate supported provider before spending.
    sha = code_checkpoint(Path(__file__).resolve().parents[3])
    budget = BudgetLedger(directory, total_usd=Decimal(os.environ['JUDGE_BUDGET_TOTAL_USD']),
                          per_run_usd=Decimal(os.environ['JUDGE_BUDGET_RUN_USD']))
    return EvaluationRuntime(config, GatewayJudge(os.environ.get('AI_GATEWAY_API_KEY', '')),
                             budget, RunRepository(directory), sha)
