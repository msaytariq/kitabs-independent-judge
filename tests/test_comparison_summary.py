"""Reporting must not turn repeated model votes into confirmed human edits."""
from copy import deepcopy
import pytest
from independent_judge.domain.scope import text_hash
from independent_judge.domain.errors import InputError
from independent_judge.domain.comparison_summary import summarize_comparison, finding_id


def record():
    texts = {'source': 'First claim. Second claim.', 'a': 'One claim. Other claim.',
             'b': 'First statement. Second statement.'}
    scope = {'texts': texts, 'hashes': {k: text_hash(v) for k, v in texts.items()},
             'profile': 'general', 'source_language': 'en', 'target_language': 'en'}
    first = {'code': 'K', 'source_excerpt': 'First claim.', 'current_text': 'One claim.',
             'should_be': 'First claim.', 'why': 'Changed meaning.', 'repeated': True}
    note = {'code': 'A', 'source_excerpt': 'Second claim.', 'current_text': 'Other claim.',
            'should_be': 'Add attribution.', 'why': 'Check source attribution.', 'repeated': False}
    return {'id': 'example', 'scope': scope, 'run': {'id': 'saved', 'status': 'needs_review',
        'manifest': {'scope': deepcopy(scope)}, 'findings': {'a': [first, note], 'b': []},
        'passes': {'a': [[first, note]] * 3}, 'scores': {'a': {'K': 999}}}, 'annotations': {}}


def test_only_unique_final_findings_count_and_apparatus_is_separate():
    data = record()
    data['run']['findings']['a'].append(deepcopy(data['run']['findings']['a'][0]))
    result = summarize_comparison(data)
    a = result['sides']['a']
    assert a['candidates'] == 2
    assert a['text_candidates'] == 1
    assert a['apparatus_candidates'] == 1
    assert a['by_code'] == {'K': 1, 'T': 0, 'A': 1, 'S': 0}
    assert a['repeated'] == 1
    assert a['necessary_edits'] is None
    assert result['sides']['b']['necessary_edits'] is None
    assert result['source_chars'] == 26
    assert result['negotiation_grade'] is False


def test_disputed_candidates_remain_visible_but_never_become_confirmed():
    data = record()
    key = finding_id('a', data['run']['findings']['a'][0])
    data['annotations'][key] = {'status': 'disputed', 'why_ru': 'Есть другое прочтение.'}
    out = summarize_comparison(data)
    assert out['sides']['a']['disputed'] == 1
    assert out['findings'][0]['status'] == 'disputed'
    assert out['sides']['a']['candidates'] == 2
    assert out['sides']['a']['necessary_edits'] is None
    assert out['findings'][0]['anchors']['source']['ranges'] == [{'start': 0, 'end': 12}]


def test_unlocated_and_conflicting_evidence_cannot_inflate_a_category():
    data = record()
    duplicate = deepcopy(data['run']['findings']['a'][0])
    duplicate['code'] = 'S'
    data['run']['findings']['a'].extend([duplicate, {**duplicate, 'current_text': 'absent quote'}])
    out = summarize_comparison(data)
    assert out['sides']['a']['by_code'] == {'K': 0, 'T': 0, 'A': 1, 'S': 0}
    assert out['sides']['a']['unlocated'] == 1
    assert out['sides']['a']['classification_conflicts'] == 1
    assert out['sides']['a']['candidates'] == 2


def test_unmeasured_is_not_zero_and_swapping_sides_is_symmetric():
    data = record()
    before = summarize_comparison(data)
    data['scope']['texts']['a'], data['scope']['texts']['b'] = data['scope']['texts']['b'], data['scope']['texts']['a']
    data['scope']['hashes'] = {k: text_hash(v) for k, v in data['scope']['texts'].items()}
    data['run']['manifest']['scope'] = deepcopy(data['scope'])
    data['run']['findings']['a'], data['run']['findings']['b'] = data['run']['findings']['b'], data['run']['findings']['a']
    assert summarize_comparison(data)['sides']['b'] == before['sides']['a']
    data['run'] = None
    assert summarize_comparison(data)['sides']['a']['candidates'] is None


@pytest.mark.parametrize('mutation', ['text', 'language', 'hash'])
def test_saved_report_must_belong_to_this_exact_scope(mutation):
    data = record()
    if mutation == 'text': data['scope']['texts']['source'] += ' extra'
    if mutation == 'hash': data['run']['manifest']['scope']['hashes']['a'] = 'bad'
    if mutation == 'language': data['scope']['target_language'] = 'ru'
    with pytest.raises(InputError): summarize_comparison(data)


def test_rounding_cannot_promote_a_short_sample_to_negotiation_grade():
    data = record()
    data['run'] = None
    data['scope']['texts']['source'] = 'x' * 5399
    data['scope']['hashes']['source'] = text_hash('x' * 5399)
    assert summarize_comparison(data)['negotiation_grade'] is False
