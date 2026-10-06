"""The edition block: what a reader gets besides the translation; it is not part of the quality total."""
from independent_judge.domain.edition import edition_readiness

B = ('He prayed.[1]\n\n[1] Narrated by Muslim.\n\n## Glossary\n\n- Ihsan: excellence\n\n'
     '## Persons\n\n- al-Hasan — scholar of Basra')


def test_each_side_gets_the_parts_of_an_edition_that_it_has():
    result = edition_readiness({'a': 'He prayed (Muslim).', 'b': B}, done_edits={'a': 0, 'b': 69},
                               typeset={'status': 'done', 'url': 'api/pipeline-b/r/typeset.pdf'})
    assert result['checks'] == {'a': 0, 'b': 4} and result['total'] == 4
    rows = {r['key']: r for r in result['rows']}
    assert (rows['notes']['a'], rows['notes']['b']) == (0, 1)
    assert (rows['glossary']['b'], rows['persons']['b']) == (1, 1)
    assert rows['typeset'] == {'key': 'typeset', 'a': None, 'b': 'done'}
    assert rows['edits'] == {'key': 'edits', 'a': 0, 'b': 69}
    assert result['download'] == 'api/pipeline-b/r/typeset.pdf' and result['in_total'] is False


def test_without_a_typeset_order_the_typeset_check_is_not_counted_as_done():
    result = edition_readiness({'a': 'x', 'b': B}, done_edits={'a': 0, 'b': 0}, typeset=None)
    assert result['checks']['b'] == 3 and result['download'] is None
