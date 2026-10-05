from independent_judge.application.comparison_view import _view
from test_comparison_summary import record


def test_view_exposes_processing_separately_from_judge_findings():
    view = _view(record())
    assert view['processing_effort']['sides']['a']['total_seconds'] is None
    assert view['paired'] is None


def test_paired_result_is_not_recomputed_with_legacy_penalties():
    data = record()
    data['run']['manifest']['protocol_version'] = 'paired-rubric-v1'
    data['run']['status'] = 'completed'
    data['run']['paired'] = {'version': 'paired-rubric-v1', 'criteria': [], 'advantage': 'none'}
    view = _view(data)
    assert view['paired'] == data['run']['paired']
    assert view['ratings']['sides']['a']['total'] is None
