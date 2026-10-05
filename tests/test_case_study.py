"""The case study shows what the judge caught and what Kitabs corrected, with quotations."""
from independent_judge.domain.case_study import case_study


def evidence(id, kind='defect', verified=True, criterion=''):
    return {'id': id, 'kind': kind, 'verified': verified, 'source_quote': f'src {id}',
            'translation_quote': f'tr {id}', 'explanation_en': f'why {id}', 'explanation_ru': f'почему {id}'}


def side(*items):
    return {'score': 3, 'status': 'assessed', 'explanation_en': '', 'explanation_ru': '', 'evidence': list(items)}


RUBRIC = {'criteria': [
    {'criterion': 'readability', 'a': side(evidence('r1')), 'b': side()},
    {'criterion': 'accuracy', 'a': side(evidence('x1'), evidence('s1', kind='strength')),
     'b': side(evidence('x2'), evidence('x3', verified=False))},
    {'criterion': 'completeness', 'a': side(evidence('x1'), evidence('c1'), evidence('c2')), 'b': side()},
]}


def op(stage, before, after, chunk='c0'):
    return {'stage': stage, 'chunk_id': chunk, 'edit_id': before, 'before': before, 'after': after}


def test_defects_come_first_by_criterion_importance_once_each_and_at_most_three():
    result = case_study(RUBRIC, None)
    assert [d['id'] for d in result['a']] == ['x1', 'c1', 'c2']
    assert result['a'][0] == {'id': 'x1', 'criterion': 'accuracy', 'source_quote': 'src x1',
                              'translation_quote': 'tr x1', 'explanation_en': 'why x1', 'explanation_ru': 'почему x1'}
    # An unverified quotation and a strength are not a caught error.
    assert [d['id'] for d in result['b']] == ['x2']


def test_kitabs_corrections_show_short_audit_edits_first():
    processing = {'sides': {'b': {'operations': [
        op('editor', 'a', 'b'), op('audit', 'x' * 400, 'y'), op('audit', 'came and be with us', 'came to us'),
        op('audit', 'the king', 'the boy'), op('audit', 'one', 'two')]}}}
    corrections = case_study(RUBRIC, processing)['kitabs_corrections']
    assert corrections == [{'stage': 'audit', 'before': 'came and be with us', 'after': 'came to us'},
                           {'stage': 'audit', 'before': 'the king', 'after': 'the boy'}]


def test_no_rubric_gives_no_case_study():
    assert case_study(None, None) is None
    assert case_study(RUBRIC, None)['kitabs_corrections'] == []
