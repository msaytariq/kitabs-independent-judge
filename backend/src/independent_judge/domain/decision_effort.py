"""Decision-time hypothesis, separate from measured time and necessary edits."""
SECONDS_PER_DECISION = 5


def _history(record: dict, side: str) -> dict | None:
    history = record.get('human_work') or {}
    if history.get('scope_hashes') != record['scope']['hashes']:
        return None
    packet = history.get('sides', {}).get(side, {})
    if packet.get('complete') is not True or not isinstance(packet.get('decisions'), list):
        return None
    unique = {}
    for event in packet['decisions']:
        key, status = event.get('id'), event.get('status')
        if not isinstance(key, str) or not key or status not in ('accepted', 'rejected'):
            return None
        if key in unique and unique[key] != status:
            return None
        unique[key] = status
    return {status: sum(v == status for v in unique.values()) for status in ('accepted', 'rejected')}


def decision_effort(record: dict, summary: dict) -> dict:
    sides = {}
    for side in ('a', 'b'):
        history = _history(record, side)
        prior = sum(history.values()) if history is not None else None
        candidates = {f['id'] for f in summary['findings'] if f['side'] == side
                      and f['status'] == 'unreviewed' and f['code'] in 'KTAS'}
        remaining = len(candidates) if summary['measured'] else None
        sides[side] = {
            'prior_decisions': prior,
            'accepted': history['accepted'] if history is not None else None,
            'rejected': history['rejected'] if history is not None else None,
            'prior_estimated_seconds': prior * SECONDS_PER_DECISION if prior is not None else None,
            'remaining_candidates': remaining,
            'remaining_estimated_seconds': remaining * SECONDS_PER_DECISION if remaining is not None else None,
            'total_estimated_seconds': (prior + remaining) * SECONDS_PER_DECISION
                if prior is not None and remaining is not None else None,
            'measured_seconds': None,
        }
    a, b = (sides[s]['remaining_candidates'] for s in ('a', 'b'))
    return {'version': 'decision-hypothesis-5s-v1', 'seconds_per_decision': SECONDS_PER_DECISION,
            'kind': 'estimate', 'sides': sides,
            'remaining_reduction_percent': round(100 * (1 - b / a), 1) if a and b is not None else None}
