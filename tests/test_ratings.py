from copy import deepcopy
import pytest
from independent_judge.domain import comparison_summary
from test_comparison_summary import record


def rating(data):
    from independent_judge.domain.ratings import comparison_ratings
    return comparison_ratings(data, comparison_summary.summarize_comparison(data))


def supported():
    data = record()
    data['run']['manifest']['protocol_version'] = 'blind-3pass-exact-consensus-v1'
    return data


def test_legacy_scale_is_exact_and_rejects_invalid_values():
    from independent_judge.domain.ratings import scale_legacy
    assert scale_legacy(7.3) == 73
    assert scale_legacy(0) == 0
    assert scale_legacy(10) == 100
    assert scale_legacy(None) is None
    for value in (-1, 11, float('nan')):
        with pytest.raises(ValueError): scale_legacy(value)


def test_missing_or_unknown_protocol_does_not_invent_perfect_scores():
    data = record()
    assert rating(data)['sides']['a']['total'] is None
    data['run'] = None
    assert rating(data)['winner'] is None


def test_bounds_and_diagnostic_criteria_are_not_averaged_again():
    out = rating(supported())
    assert out['sides']['a']['accuracy'] == 0
    assert out['sides']['a']['terminology'] == 100
    assert out['sides']['a']['readability'] == 100
    assert out['sides']['b']['accuracy'] == 100
    assert out['sides']['b']['total'] == 70
    assert out['winner'] == 'b'
    assert out['kind'] == 'provisional_machine_index'


def test_identical_evidence_ties_and_swapping_sides_preserves_values():
    data = supported()
    before = rating(data)
    for key in ('texts', 'hashes'):
        data['scope'][key]['a'], data['scope'][key]['b'] = data['scope'][key]['b'], data['scope'][key]['a']
    data['run']['manifest']['scope'] = deepcopy(data['scope'])
    data['run']['findings']['a'], data['run']['findings']['b'] = data['run']['findings']['b'], data['run']['findings']['a']
    after = rating(data)
    assert after['sides']['a'] == before['sides']['b']
    assert after['winner'] == 'a'
    data['scope']['texts']['a'] = data['scope']['texts']['b']
    data['scope']['hashes']['a'] = data['scope']['hashes']['b']
    data['run']['manifest']['scope'] = deepcopy(data['scope'])
    data['run']['findings']['a'] = deepcopy(data['run']['findings']['b'])
    assert rating(data)['winner'] == 'tie'


def test_disputed_or_unlocated_evidence_is_excluded_and_disclosed():
    data = supported()
    finding = data['run']['findings']['a'][0]
    data['annotations'][comparison_summary.finding_id('a', finding)] = {'status': 'disputed'}
    out = rating(data)
    assert out['sides']['a']['accuracy'] == 100
    assert out['sides']['a']['excluded'] == 1
    finding['current_text'] = 'absent'
    assert rating(data)['sides']['a']['excluded'] == 1


def test_apparatus_is_structure_only_and_unattached_markers_add_no_notes():
    from independent_judge.domain.apparatus_inventory import inventory, structural_score
    assert structural_score(inventory('Text [1] with no note.'), source_notes=1) == 0
    items = inventory('Text.\n[1] A note.\n## Glossary\n- Term: definition.\n## Persons\n- Someone: biography.')
    assert structural_score(items, source_notes=2) == 75
    data = supported()
    text = 'Text.\n[1] Irrelevant note.\n## Glossary\n- Term: unrelated.'
    data['scope']['texts']['b'] = text
    from independent_judge.domain.scope import text_hash
    data['scope']['hashes']['b'] = text_hash(text)
    data['run']['manifest']['scope'] = deepcopy(data['scope'])
    result = rating(data)['sides']['b']
    assert result['apparatus_correctness'] is None
    assert result['apparatus_basis'] == 'structure_only_relevance_unverified'
