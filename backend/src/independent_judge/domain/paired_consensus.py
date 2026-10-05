"""Map both passes to canonical sides; preserve disagreements, never average."""
from independent_judge.domain.paired_rubric import RUBRIC, VERSION


def reconcile_assessments(passes: list[dict], scope) -> dict:
    if len(passes) != 2:
        raise ValueError('Exactly two completed passes are required')
    indexed = [{r['criterion']: r for r in p['criteria']} for p in passes]
    rows, defects = [], {'a': set(), 'b': set()}
    for criterion in RUBRIC:
        row = {'criterion': criterion}
        for side in ('a', 'b'):
            a, b = (p[criterion][side] for p in indexed)
            stable = a['status'] == b['status'] and a['score'] == b['score']
            evidence = []
            seen = set()
            for pass_number, value in enumerate((a, b), 1):
                for item in value['evidence']:
                    key = (item['id'], item['kind'], item['explanation_en'], item['explanation_ru'])
                    if item['verified'] and item['kind'] == 'defect':
                        defects[side].add(item['id'])
                    if key not in seen:
                        evidence.append(item | {'pass': pass_number})
                        seen.add(key)
            row[side] = {'score': a['score'] if stable else None,
                         'status': a['status'] if stable else 'unstable',
                         'pass_scores': [a.get('proposed_score', a['score']), b.get('proposed_score', b['score'])],
                         'coverage': [a['coverage'], b['coverage']], 'evidence': evidence,
                         'explanations': [{k: value[k] for k in ('explanation_en', 'explanation_ru')} for value in (a, b)]}
        if scope.texts['a'] == scope.texts['b'] and any(row['a'][key] != row['b'][key] for key in ('score', 'status')):
            for side in ('a', 'b'):
                row[side].update(score=None, status='unstable', symmetry_conflict=True)
        rows.append(row)
    signs = []
    complete = True
    for row in rows:
        a, b = row['a'], row['b']
        if a['status'] == b['status'] == 'not_applicable':
            continue
        if a['score'] is None or b['score'] is None:
            complete = False
        else:
            signs.append((a['score'] > b['score']) - (a['score'] < b['score']))
    advantage = 'none'
    if complete:
        advantage = 'mixed' if 1 in signs and -1 in signs else 'a' if 1 in signs else 'b' if -1 in signs else 'none'
    return {'version': VERSION, 'kind': 'machine_assessment', 'criteria': rows, 'advantage': advantage,
            'unique_defects': {s: len(v) for s, v in defects.items()},
            'external_references': 'not_checked', 'panel': 'two_orders_one_model'}
