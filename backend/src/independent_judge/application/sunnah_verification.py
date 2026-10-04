"""Confirm candidate references against actual Sunnah Arabic text, not numbers alone."""
from independent_judge.domain.hadith_matching import correspondence
from independent_judge.reference_ports import LibraryUnavailable


def verify_official(items: list[dict], source) -> dict:
    if source is None: return {'source': 'Sunnah.com', 'status': 'requires_key', 'records': []}
    checked, seen, limited = [], {}, False
    for item in items:
        for candidate in item['candidates']:
            collection, number = candidate['id'].split(':', 1)
            identity = (collection, number)
            if identity not in seen:
                if len(seen) >= 10:
                    limited = True
                    continue
                try: seen[identity] = source.lookup(collection, number)
                except LibraryUnavailable: seen[identity] = 'unavailable'
            record = seen[identity]
            if record == 'unavailable': state = 'unavailable'
            elif record is None: state = 'not_found'
            else: state, _ = correspondence(item['quote'], record['text'])
            checked.append({'quote': item['quote'], 'candidate_id': candidate['id'],
                            'status': state, 'record': record if isinstance(record, dict) else None})
    unavailable = sum(c['status'] == 'unavailable' for c in checked)
    status = ('no_candidates' if not checked else 'unavailable' if unavailable == len(checked)
              else 'partial' if unavailable or limited else 'checked')
    return {'source': 'Sunnah.com', 'status': status, 'records': checked,
            'lookup_limit': 10, 'lookups': len(seen), 'limit_reached': limited}
