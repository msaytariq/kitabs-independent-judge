"""Negative cases beyond the happy protocol: uncertain evidence and budget overruns."""
from decimal import Decimal
from dataclasses import replace
import pytest
from independent_judge.domain.evaluation import EvaluationError,JudgeConfig
from independent_judge.domain.judge_prompt import assessment_prompt
from independent_judge.domain.budget import reservation
from independent_judge.domain.review_parsing import decisions,CriticalDecision,CrossDecision
from independent_judge.domain.completeness import parse_units,Coverage,validate_inventory,reconcile_coverage
from independent_judge.infrastructure.budget_repository import BudgetLedger
from test_judge_contracts import sample


@pytest.mark.parametrize('text', ['{"decisions":[]}', '{"decisions":[{"index":0,"verdict":"keep","code":"T","why":"x"}]}'])
def test_critical_appeal_cannot_omit_or_contradict_verdict(text):
    with pytest.raises(EvaluationError): decisions(text,1,CriticalDecision)


def test_cross_check_cannot_claim_present_without_evidence():
    with pytest.raises(EvaluationError):
        decisions('{"decisions":[{"index":0,"verdict":"present","finding":null,"why":"x"}]}',1,CrossDecision)


def test_coverage_conflict_and_missing_quote_require_review():
    a={'id':0,'status':'conveyed','quote':'hello','why':'x'}
    result=reconcile_coverage([[a],[a | {'status':'missing','quote':''}]],'hello')
    assert result['counts']['needs_review']==1
    assert reconcile_coverage([[a],[a]],'elsewhere')['counts']['needs_review']==1
    with pytest.raises(EvaluationError): parse_units('{"units":[]}',Coverage,1)
    with pytest.raises(EvaluationError): validate_inventory([{'source_excerpt':'repeat'}],'repeat repeat')


def test_actual_cost_above_reserve_is_recorded_and_halts_next_request(tmp_path):
    l=BudgetLedger(tmp_path,total_usd=Decimal('3'),per_run_usd=Decimal('1'))
    l.reserve('r','a',Decimal('.01'))
    with pytest.raises(EvaluationError): l.settle('r','a',Decimal('.02'))
    assert l.summary()['reported_usd']=='0.020000'
    with pytest.raises(EvaluationError): l.reserve('new','b',Decimal('.01'))


def test_unreviewed_cost_configuration_is_blocked_before_gateway():
    with pytest.raises(EvaluationError):
        reservation(assessment_prompt(sample(),'a'),replace(JudgeConfig(),output_usd_per_million='0'))
