"""Boundary selections preserve originals; semantic alignment stays attributed."""
import pytest
from independent_judge.domain.scope import text_hash
from independent_judge.domain.errors import InputError
from independent_judge.domain.corpus_boundaries import verify_boundary_selection


def selected():
    full = {'source': 'قبل. ألف. باء. بعد.', 'a': 'Before. One. Two. After.',
            'b': 'Intro. First. Second. End.'}
    quotes = {'source': ('ألف.', 'باء.'), 'a': ('One.', 'Two.'), 'b': ('First.', 'Second.')}
    ranges = {k: {'start': full[k].index(start), 'end': full[k].index(end) + len(end),
                  'input_sha256': text_hash(full[k]), 'start_quote': start, 'end_quote': end}
              for k, (start, end) in quotes.items()}
    return full, ranges


def test_exact_ranges_preserve_full_source_and_share_named_semantic_boundaries():
    full, ranges = selected()
    out = verify_boundary_selection(full, ranges)
    assert out['texts'] == {'source': 'ألف. باء.', 'a': 'One. Two.', 'b': 'First. Second.'}
    assert out['ranges']['a']['start'] == 8
    assert full['source'] == 'قبل. ألف. باء. بعد.'


@pytest.mark.parametrize('problem', ['short_end', 'stale', 'moved_start', 'past_end'])
def test_truncated_or_stale_selection_cannot_pass_on_length_alone(problem):
    full, ranges = selected()
    if problem == 'short_end': ranges['source']['end'] -= 5
    if problem == 'stale': full['source'] += ' جديد'
    if problem == 'moved_start': ranges['a']['start'] += 1
    if problem == 'past_end': ranges['b']['end'] = 9999
    with pytest.raises(InputError): verify_boundary_selection(full, ranges)
