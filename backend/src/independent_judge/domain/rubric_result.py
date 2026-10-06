"""One definite grade per criterion, a simple total and a winner for the jury table."""
from independent_judge.domain.paired_rubric import RUBRIC

VERSION = 'rubric-v1'


def summarize_assessment(assessment: dict) -> dict:
    indexed = {row['criterion']: row for row in assessment['criteria']}
    rows, scored, defects = [], {'a': [], 'b': []}, {'a': set(), 'b': set()}
    for criterion in RUBRIC:
        row = {'criterion': criterion}
        for side in ('a', 'b'):
            value = indexed[criterion][side]
            located = [e for e in value['evidence'] if e['verified']]
            defects[side].update(e['id'] for e in located if e['kind'] == 'defect')
            row[side] = {'score': value['score'], 'status': value['status'],
                         'explanation_en': value['explanation_en'], 'explanation_ru': value['explanation_ru'],
                         'evidence': located}
        # The total compares like with like: only criteria graded for both sides.
        if row['a']['score'] is not None and row['b']['score'] is not None:
            for side in ('a', 'b'):
                scored[side].append(row[side]['score'])
        rows.append(row)
    totals = {side: round(sum(v) / len(v), 1) if v else None for side, v in scored.items()}
    winner = None
    if totals['a'] is not None:
        winner = 'tie' if totals['a'] == totals['b'] else 'a' if totals['a'] > totals['b'] else 'b'
    return {'version': VERSION, 'kind': 'machine_assessment', 'criteria': rows, 'totals': totals,
            'winner': winner, 'unique_defects': {s: len(v) for s, v in defects.items()},
            'critical_errors': _critical(assessment.get('critical_errors'))}


def _critical(errors: list | None) -> dict | None:
    """Critical errors whose two quotes the code found, each error once; None for an earlier rubric."""
    if errors is None:
        return None
    sides = {'a': {}, 'b': {}}
    for error in errors:
        if error['verified']:
            sides[error['side']].setdefault(error['id'], error)
    return {side: list(found.values()) for side, found in sides.items()}
