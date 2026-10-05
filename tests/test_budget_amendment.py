from decimal import Decimal
import pytest
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.domain.evaluation import EvaluationError


def test_authorized_amendment_preserves_spend_and_outstanding_reservations(tmp_path):
    old = BudgetLedger(tmp_path, total_usd=Decimal('1'), per_run_usd=Decimal('1'))
    old.reserve('past', 'paid', Decimal('.5'))
    old.settle('past', 'paid', Decimal('.415857'))
    old.reserve('past', 'pending', Decimal('.2'))
    old.amend_policy(expected_total=Decimal('1'), expected_per_run=Decimal('1'),
                     total=Decimal('3'), per_run=Decimal('3'), authorization='Explicit test-series approval')
    new = BudgetLedger(tmp_path, total_usd=Decimal('3'), per_run_usd=Decimal('3'))
    assert new.summary()['reported_usd'] == '0.415857'
    assert new.summary()['unresolved_reserved_usd'] == '0.200000'
    assert old.summary()['total_limit_usd'] == '3.000000'
    new.reserve('next', 'one', Decimal('2.3'))
    with pytest.raises(EvaluationError, match='exceed'):
        old.reserve('next', 'two', Decimal('.1'))


def test_amendment_requires_matching_old_policy_and_cannot_erase_commitments(tmp_path):
    ledger = BudgetLedger(tmp_path, total_usd=Decimal('1'), per_run_usd=Decimal('1'))
    ledger.reserve('r', 'c', Decimal('.5'))
    for expected, total in [('2', '3'), ('1', '.1')]:
        with pytest.raises(EvaluationError):
            ledger.amend_policy(expected_total=Decimal(expected), expected_per_run=Decimal('1'),
                                total=Decimal(total), per_run=Decimal(total), authorization='test')
    assert ledger.summary()['total_limit_usd'] == '1.000000'
