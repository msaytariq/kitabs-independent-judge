from independent_judge.application.comparison_view import _view
from test_comparison_summary import record


def test_view_exposes_processing_separately_from_judge_findings():
    view = _view(record())
    assert view['processing_effort']['sides']['a']['total_seconds'] is None
    assert view['rubric'] is None


def test_rubric_result_is_not_recomputed_with_legacy_penalties():
    data = record()
    data['run']['manifest']['protocol_version'] = 'rubric-v1'
    data['run']['status'] = 'completed'
    data['run']['rubric'] = {'version': 'rubric-v1', 'criteria': [], 'totals': {'a': None, 'b': None}, 'winner': None}
    view = _view(data)
    assert view['rubric'] == data['run']['rubric']
    assert view['rubric_protocol'] is True
    assert view['ratings']['sides']['a']['total'] is None


def _packet(job_id, end, hashes):
    return {'b': {'job_id': job_id, 'state': 'completed', 'source_sha256': hashes['source'],
                  'text_sha256': hashes['b'], 'timing_complete': True,
                  'intervals': [{'start': 0, 'end': end}], 'operations_complete': True, 'operations': []}}


def test_cached_saved_run_never_replaces_the_current_job_measurement():
    from independent_judge.application.comparison_view import ComparisonViewService
    saved = record()
    hashes = saved['scope']['hashes']
    saved['processing'] = _packet('old-job', 10, hashes)
    scope = saved['scope'] | {'status': 'ready', 'processing': _packet('new-job', 90, hashes)}

    class Catalog:
        def records(self): return [saved]
        def get(self, _): return saved

    class Scopes:
        def get(self, _): return scope

    view = ComparisonViewService(Catalog(), Scopes(), renderer=str).scope('scope-1')
    assert view['matched_example_id'] == 'example'
    b = view['processing_effort']['sides']['b']
    assert b['job_id'] == 'new-job' and b['pipeline_seconds'] == 90


def test_cached_saved_run_without_current_job_does_not_import_its_time():
    from independent_judge.application.comparison_view import ComparisonViewService
    saved = record()
    saved['processing'] = _packet('old-job', 10, saved['scope']['hashes'])
    scope = saved['scope'] | {'status': 'ready'}

    class Catalog:
        def records(self): return [saved]

    class Scopes:
        def get(self, _): return scope

    view = ComparisonViewService(Catalog(), Scopes(), renderer=str).scope('scope-1')
    assert view['processing_effort']['sides']['b']['total_seconds'] is None
    assert view['processing_effort']['sides']['b']['job_id'] is None


def test_saved_reference_check_is_kept_when_no_newer_check_exists():
    from independent_judge.application.comparison_view import ComparisonViewService
    saved = record() | {'hadith': {'status': 'checked', 'quran': {'found': 1}}}

    class Jobs:
        def reference(self, key): return None

    service = ComparisonViewService(None, None, renderer=str, jobs=Jobs())
    assert service.project(saved)['hadith']['status'] == 'checked'


def test_view_gives_points_remaining_work_and_summary_for_a_rubric_run():
    from test_rubric_report import rubric_record
    view = _view(rubric_record())
    assert view['jury']['totals'] == {'a': 38, 'b': 75} and view['jury']['winner'] == 'b'
    assert view['effort_reduction']['a']['minutes'] == 3 and view['effort_reduction']['reduction_percent'] == 100
    assert view['jury_summary']['en'][0] == 'Translation B is better: 75 against 38 points.'


def test_view_without_a_finished_rubric_has_no_points():
    view = _view(record())
    assert view['jury'] is None and view['effort_reduction'] is None and view['jury_summary'] is None


def test_view_gives_the_case_study_of_a_rubric_run():
    from test_rubric_report import rubric_record
    study = _view(rubric_record())['case_study']
    assert [d['id'] for d in study['a']] == ['e1'] and study['a'][0]['criterion'] == 'accuracy'
    assert study['kitabs_corrections'] == []
    assert _view(record())['case_study'] is None


def test_view_compares_the_second_judge_on_the_same_criteria():
    from test_rubric_report import rubric_record
    data = rubric_record()
    data['run']['manifest']['actual_models'] = ['google/gemini-3.8-flash']
    second = {'model': 'spacexai/grok-4.1-fast-reasoning', 'run_id': 'second', 'rubric': data['run']['rubric']}
    view = _view(data | {'second_judge': second})
    assert view['second_judge']['agree'] is True
    assert view['second_judge']['first']['model'] == 'google/gemini-3.8-flash'
    assert view['second_judge']['second']['totals'] == {'a': 38, 'b': 75}
    assert _view(data)['second_judge'] is None


def test_view_adds_the_takhrij_row_from_the_saved_reference_check():
    from test_rubric_report import rubric_record
    takhrij = {'version': 'takhrij-v1', 'total': 4, 'a': {'delivered': 0, 'wrong': 2, 'items': []},
               'b': {'delivered': 4, 'wrong': 0, 'items': []}}
    view = _view(rubric_record() | {'hadith': {'status': 'checked', 'takhrij': takhrij}})
    assert view['takhrij'] == takhrij
    assert [r['key'] for r in view['jury']['rows']][-1] == 'takhrij'
    assert view['effort_reduction']['a']['references'] == 6
