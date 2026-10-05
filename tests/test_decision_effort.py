from copy import deepcopy
import pytest
from independent_judge.domain.comparison_summary import summarize_comparison
from test_comparison_summary import record


def estimate(data):
    from independent_judge.domain.decision_effort import decision_effort
    return decision_effort(data, summarize_comparison(data))


def history(data, decisions):
    data['human_work'] = {'scope_hashes': deepcopy(data['scope']['hashes']),
                         'sides': {'b': {'complete': True, 'decisions': decisions}}}


def test_twelve_unique_decisions_are_sixty_seconds_and_retries_do_not_count():
    data = record()
    events = [{'id': str(i), 'status': 'accepted' if i % 2 else 'rejected'} for i in range(12)]
    history(data, events + events)
    out = estimate(data)
    assert out['seconds_per_decision'] == 5
    assert out['sides']['b']['prior_decisions'] == 12
    assert out['sides']['b']['prior_estimated_seconds'] == 60
    assert out['sides']['b']['accepted'] == 6
    assert out['sides']['b']['rejected'] == 6


def test_unknown_history_and_remaining_candidates_are_separate():
    out = estimate(record())
    assert out['sides']['a']['prior_decisions'] is None
    assert out['sides']['a']['remaining_candidates'] == 2
    assert out['sides']['a']['remaining_estimated_seconds'] == 10
    assert out['sides']['a']['measured_seconds'] is None
    assert out['sides']['a']['total_estimated_seconds'] is None


def test_zero_history_requires_explicit_complete_records_and_matching_artifacts():
    data = record()
    history(data, [])
    assert estimate(data)['sides']['b']['prior_decisions'] == 0
    data['human_work']['scope_hashes']['b'] = 'other-artifact'
    assert estimate(data)['sides']['b']['prior_decisions'] is None


def test_unknown_and_zero_denominators_and_b_with_more_work():
    data = record()
    out = estimate(data)
    assert out['remaining_reduction_percent'] == 100
    data['run']['findings']['a'] = []
    assert estimate(data)['remaining_reduction_percent'] is None
    data['run'] = None
    assert estimate(data)['sides']['b']['remaining_estimated_seconds'] is None


def test_conflicting_replayed_decisions_do_not_invent_a_history():
    data = record()
    history(data, [{'id':'same','status':'accepted'}, {'id':'same','status':'rejected'}])
    assert estimate(data)['sides']['b']['prior_decisions'] is None
