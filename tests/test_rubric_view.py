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
