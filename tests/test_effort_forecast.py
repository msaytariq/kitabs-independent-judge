"""The forecast cannot turn counts into measured minutes or hide uncertainty."""
from copy import deepcopy
from independent_judge.application.comparison_view import _view
from test_comparison_summary import record


def test_api_automatically_forecasts_remaining_work_including_apparatus():
    view = _view(record())
    forecast = view.get('effort')
    assert forecast is not None, 'Comparison must include an automatic forecast'
    assert forecast['kind'] == 'forecast'
    assert forecast['sides']['a']['edits'] == 2
    assert forecast['sides']['a']['units'] == 9
    assert forecast['sides']['b']['units'] == 0
    assert forecast['reduction_percent'] == 100
    assert forecast['measured_minutes'] is None


def test_missing_assessment_does_not_mean_no_editor_work():
    data = record(); data['run'] = None
    forecast = _view(data).get('effort')
    assert forecast is not None
    assert forecast['reduction_percent'] is None
    assert forecast['sides']['a']['edits'] is None


def test_duplicate_and_disputed_findings_cannot_inflate_savings():
    from independent_judge.domain.comparison_summary import finding_id
    data = record(); first = data['run']['findings']['a'][0]
    data['run']['findings']['a'].append(deepcopy(first))
    data['annotations'][finding_id('a', first)] = {'status': 'disputed'}
    forecast = _view(data).get('effort')
    assert forecast is not None
    assert forecast['sides']['a']['edits'] == 1
    assert forecast['sides']['a']['units'] == 4
    assert forecast['sides']['a']['excluded'] == 1


def test_uniform_work_40_vs_10_means_75_percent_not_measured_time():
    from independent_judge.domain.effort_forecast import forecast_effort
    summary = {'measured': True, 'findings': [
        {'id': f'{side}-{n}', 'side': side, 'code': 'T', 'status': 'unreviewed'}
        for side, count in [('a', 40), ('b', 10)] for n in range(count)]}
    result = forecast_effort(summary)
    assert result['edit_reduction_percent'] == 75
    assert result['reduction_percent'] == 75
    assert result['sensitivity_percent'] == [75, 75]
    assert result['calibrated'] is False


def test_shared_weight_sensitivity_and_zero_denominator():
    from independent_judge.domain.effort_forecast import forecast_effort
    summary = {'measured': True, 'findings': [
        {'id': 'a', 'side': 'a', 'code': 'S', 'status': 'unreviewed'},
        {'id': 'b', 'side': 'b', 'code': 'K', 'status': 'unreviewed'}]}
    result = forecast_effort(summary)
    assert result['reduction_percent'] == -400
    assert result['sensitivity_percent'] == [-700, -50]
    summary['findings'] = []
    assert forecast_effort(summary)['reduction_percent'] is None
