"""Applied audit/editor operations are confirmed from stage texts, not from statuses alone."""
from copy import deepcopy
from independent_judge.domain.processing_effort import processing_effort
from independent_judge.domain.scope import text_hash
from independent_judge.infrastructure.platform_processing import processing_packet

TRANSLATED = 'Alpha one. Beta two. Gamma three.'
AUDITED = 'Alpha one. Beta 2. Gamma three.'
EDITED = 'Alpha first. Beta 2. Gamma three.'
FINAL = 'Alpha first. Beta 2. Gamma three!'


def artifact(stage, kind, payload, n):
    return {'id': f'{stage}-art', 'jobId': 'job', 'stageId': stage, 'kind': kind, 'chunkId': 'c1',
            'hash': str(n) * 64, 'payload': payload}


def artifacts():
    return [
        artifact('audit', 'audit_report', {'translatedText': TRANSLATED, 'issues': [
            {'currentText': 'Beta two', 'revisedText': 'Beta 2'},
            {'currentText': 'Gamma three', 'revisedText': None}]}, 1),
        artifact('editor', 'edited_chunk', {'inputText': AUDITED, 'editedText': EDITED, 'issues': [
            {'currentText': 'Alpha one', 'revisedText': 'Alpha first'},
            {'currentText': 'Beta 2', 'revisedText': 'Beta 2'}]}, 2),
        artifact('proofreader', 'proofread_chunk', {'inputText': EDITED, 'proofreadText': FINAL, 'issues': [
            {'currentText': 'three.', 'revisedText': 'three!'}]}, 3)]


def reviews():
    return [{'stage_id': 'audit', 'chunk_id': 'c1', 'issue_index': 0, 'status': 'accepted'},
            {'stage_id': 'audit', 'chunk_id': 'c1', 'issue_index': 1, 'status': 'rejected'},
            {'stage_id': 'editor', 'chunk_id': 'c1', 'issue_index': 0, 'status': 'accepted'},
            {'stage_id': 'editor', 'chunk_id': 'c1', 'issue_index': 1, 'status': 'accepted'},
            {'stage_id': 'proofreader', 'chunk_id': 'c1', 'issue_index': 0, 'status': 'accepted'}]


def packet(**changes):
    args = {'job_id': 'job', 'artifacts': artifacts(), 'reviews': reviews(),
            'intervals': [{'start': 100.0, 'end': 340.5}], 'source_sha256': 's' * 64, 'b_text': FINAL} | changes
    return processing_packet(**args)


def effort(data):
    record = {'scope': {'hashes': {'source': 's' * 64, 'a': 'a', 'b': text_hash(FINAL)}}, 'processing': {'b': data}}
    return processing_effort(record)['sides']['b']


def test_confirmed_audit_and_editor_edits_enter_the_formula_once():
    result = effort(packet())
    assert result['pipeline_seconds'] == 240.5
    assert result['audit_operations'] == 1
    assert result['editor_operations'] == 1  # the no-op edit does not count
    assert result['total_seconds'] == 250.5
    assert [op['before'] for op in result['operations']] == ['Beta two', 'Alpha one']


def test_proofreader_edits_and_rejected_findings_are_not_operations():
    data = packet()
    assert {op['stage'] for op in data['operations'] if op['status'] == 'applied'} <= {'audit', 'editor'}
    assert any(op['status'] == 'rejected' for op in data['operations'])


def test_accepted_edit_missing_from_the_next_stage_text_makes_the_journal_unknown():
    broken = artifacts()
    broken[1]['payload']['inputText'] = TRANSLATED  # the audit fix never landed
    result = effort(packet(artifacts=broken))
    assert result['audit_operations'] is None and result['total_seconds'] is None
    assert result['pipeline_seconds'] == 240.5


def test_missing_review_record_or_next_stage_is_not_zero():
    assert effort(packet(reviews=reviews()[1:]))['audit_operations'] is None
    without_proofreader = artifacts()[:2]
    assert effort(packet(artifacts=without_proofreader))['editor_operations'] is None


def test_missing_timing_keeps_operations_but_no_total():
    result = effort(packet(intervals=None))
    assert result['pipeline_seconds'] is None and result['total_seconds'] is None
    assert result['audit_operations'] == 1


def test_assembly_text_must_match_b():
    assert effort(packet(b_text=FINAL + ' extra'))['job_id'] is None


def test_input_is_not_mutated():
    data, events = artifacts(), reviews()
    before = deepcopy((data, events))
    packet(artifacts=data, reviews=events)
    assert (data, events) == before
