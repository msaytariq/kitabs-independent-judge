"""Symmetric, uncalibrated effort model for remaining candidate corrections.

Units express relative complexity, not minutes. Sensitivity varies each category
weight identically for both versions; it is not a statistical confidence interval.
Reading, verification of correct text and prior human work are outside this model.
"""
from itertools import product

WEIGHTS = {'K': 5, 'T': 3, 'A': 4, 'S': 1}
BOUNDS = {'K': (3, 8), 'T': (2, 4), 'A': (3, 8), 'S': (1, 2)}


def _reduction(a: float, b: float) -> float | None:
    return round(100 * (1 - b / a), 1) if a else None


def forecast_effort(summary: dict) -> dict:
    assessed = summary['measured']
    sides = {}
    for side in ('a', 'b'):
        items = {f['id']: f for f in summary['findings'] if f['side'] == side}
        eligible = [f for f in items.values()
                    if f['status'] == 'unreviewed' and f['code'] in WEIGHTS]
        counts = {code: sum(f['code'] == code for f in eligible) for code in WEIGHTS}
        sides[side] = {'edits': len(eligible) if assessed else None,
                       'units': sum(counts[c] * WEIGHTS[c] for c in WEIGHTS) if assessed else None,
                       'by_code': counts if assessed else None,
                       'excluded': len(items) - len(eligible)}
    reduction = edit_reduction = sensitivity = None
    if assessed:
        reduction = _reduction(sides['a']['units'], sides['b']['units'])
        edit_reduction = _reduction(sides['a']['edits'], sides['b']['edits'])
        if reduction is not None:
            values = []
            for weights in product(*BOUNDS.values()):
                a, b = [sum(sides[s]['by_code'][c] * w for c, w in zip(BOUNDS, weights))
                        for s in ('a', 'b')]
                values.append(_reduction(a, b))
            sensitivity = [min(values), max(values)]
    return {'kind': 'forecast', 'calibrated': False, 'measured_minutes': None,
            'version': 'relative-correction-effort-v1', 'sides': sides,
            'reduction_percent': reduction, 'edit_reduction_percent': edit_reduction,
            'sensitivity_percent': sensitivity, 'weights': dict(WEIGHTS),
            'weight_bounds': {k: list(v) for k, v in BOUNDS.items()},
            'scope': 'remaining_candidate_corrections_only'}
