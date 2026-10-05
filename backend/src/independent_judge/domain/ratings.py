"""Versioned, provisional machine indices; never confirmed expert grades."""
import math
from independent_judge.domain.apparatus_inventory import inventory, structural_score

VERSION = 'judge-100-70-30-v1'
PROTOCOL = 'blind-3pass-exact-consensus-v1'


def scale_legacy(value: float | None) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value) or not 0 <= value <= 10:
        raise ValueError('Legacy rating must be finite and within 0–10.')
    return round(value * 10, 6)


def _index(penalty: float, pages: float) -> float:
    return scale_legacy(round(max(0, 10 - penalty / pages), 1))


def comparison_ratings(record: dict, summary: dict) -> dict:
    run = record.get('run') or {}
    pages = summary['source_chars'] / 1800
    supported = (summary['measured'] and pages > 0
                 and run.get('manifest', {}).get('protocol_version') == PROTOCOL
                 and all(side in run.get('findings', {}) for side in ('a', 'b')))
    sides = {}
    source_notes = inventory(record['scope']['texts']['source'])['notes']
    for side in ('a', 'b'):
        all_items = [f for f in summary['findings'] if f['side'] == side]
        eligible = [f for f in all_items if f['status'] == 'unreviewed' and f['code'] in 'KTAS']
        counts = {code: sum(f['code'] == code for f in eligible) for code in 'KTAS'}
        accuracy = _index(3 * counts['K'] + counts['T'] + .5 * counts['S'], pages) if supported else None
        structure = inventory(record['scope']['texts'][side])
        apparatus = structural_score(structure, source_notes=source_notes) if supported else None
        sides[side] = {
            'accuracy': accuracy,
            'terminology': _index(counts['T'], pages) if supported else None,
            'readability': _index(.5 * counts['S'], pages) if supported else None,
            'apparatus': apparatus,
            'total': scale_legacy(round(.7 * accuracy / 10 + .3 * apparatus / 10, 1)) if supported else None,
            'apparatus_correctness': None,
            'apparatus_basis': 'structure_only_relevance_unverified',
            'inventory': structure, 'excluded': len(all_items) - len(eligible),
            'finding_ids': [f['id'] for f in eligible] if supported else [],
        }
    winner = None
    if supported:
        a, b = (sides[s]['total'] for s in ('a', 'b'))
        winner = 'tie' if a == b else 'a' if a > b else 'b'
    return {'version': VERSION, 'kind': 'provisional_machine_index', 'sides': sides,
            'winner': winner, 'weights': {'accuracy': .7, 'apparatus': .3}}
