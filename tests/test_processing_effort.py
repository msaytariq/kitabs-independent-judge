from copy import deepcopy
import importlib


def record():
    return {'scope': {'hashes': {'source': 'source-hash', 'a': 'a-hash', 'b': 'b-hash'}},
            'processing': {'b': {'job_id': 'job', 'state': 'completed',
                'source_sha256': 'source-hash', 'text_sha256': 'b-hash',
                'timing_complete': True, 'intervals': [{'start': 10, 'end': 30}, {'start': 20, 'end': 50}],
                'operations_complete': True, 'operations': []}}}


def operation(**changes):
    return {'job_id': 'job', 'chunk_id': 'c1', 'stage': 'audit', 'artifact_id': 'artifact',
            'artifact_sha256': '1' * 64, 'edit_id': 'e1', 'status': 'applied',
            'execution_confirmed': True, 'before': 'was', 'after': 'is',
            'input_sha256': '2' * 64, 'output_sha256': '3' * 64,
            'receipt_sha256': '4' * 64, **changes}


def calculate(data):
    module = importlib.import_module('independent_judge.domain.processing_effort')
    return module.processing_effort(data)['sides']


def test_missing_chat_time_never_comes_from_judge_findings():
    data = record()
    data['run'] = {'findings': {'a': [{'id': 'finding'}]}}
    assert calculate(data)['a']['total_seconds'] is None
    assert calculate(data)['a']['reason'] == 'time_not_established'


def test_confirmed_zero_operations_and_overlapping_intervals():
    b = calculate(record())['b']
    assert b['pipeline_seconds'] == 40
    assert b['audit_operations'] == b['editor_operations'] == 0
    assert b['simulated_seconds'] == 0
    assert b['total_seconds'] == 40


def test_only_applied_audit_editor_operations_count_once():
    data = record()
    ops = [operation(), operation(stage='editor'), operation(stage='proofreader'),
           operation(edit_id='noop', before='same', after='same'),
           operation(edit_id='accepted', status='accepted', execution_confirmed=False),
           operation(edit_id='rejected', status='rejected', execution_confirmed=False)]
    data['processing']['b']['operations'] = ops + deepcopy(ops)
    b = calculate(data)['b']
    assert (b['audit_operations'], b['editor_operations']) == (1, 1)
    assert b['total_seconds'] == 50
    assert len(b['operations']) == 2
    assert b['operations'][0]['before'] == 'was'


def test_absent_or_unproven_journal_is_not_zero():
    data = record()
    data['processing']['b'].pop('operations_complete')
    assert calculate(data)['b']['pipeline_seconds'] == 40
    assert calculate(data)['b']['simulated_seconds'] is None
    assert calculate(data)['b']['total_seconds'] is None
    data = record()
    data['processing']['b']['operations'] = [operation(execution_confirmed=False)]
    assert calculate(data)['b']['audit_operations'] is None


def test_stale_text_or_incomplete_job_invalidates_measurement():
    for change in ({'text_sha256': 'stale'}, {'source_sha256': 'stale'}, {'state': 'running'}):
        data = record()
        data['processing']['b'].update(change)
        assert calculate(data)['b']['total_seconds'] is None
        assert calculate(data)['b']['pipeline_seconds'] is None


def test_conflicting_duplicates_invalidate_counts():
    data = record()
    data['processing']['b']['operations'] = [operation(), operation(after='different')]
    assert calculate(data)['b']['audit_operations'] is None


def test_invalid_timing_never_substitutes_model_or_browser_time():
    for intervals in ([], [{'start': 4, 'end': 2}], [{'start': 1, 'end': float('nan')}],
                      [{'start': True, 'end': 2}]):
        data = record()
        data['processing']['b']['intervals'] = intervals
        b = calculate(data)['b']
        assert b['pipeline_seconds'] is None
        assert b['simulated_seconds'] == 0
        assert b['total_seconds'] is None
