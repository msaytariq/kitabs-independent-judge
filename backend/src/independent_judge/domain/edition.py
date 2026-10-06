"""Readiness for publication: anchored notes, glossary, person index and a typeset book.

The code counts the parts in each text (apparatus_inventory); the typeset book comes from the
Kitabs launch of B. The block is shown apart and is not part of the quality total.
"""
from independent_judge.domain.apparatus_inventory import inventory

CHECKS = ('notes', 'glossary', 'persons', 'typeset')


def edition_readiness(texts: dict, *, done_edits: dict, typeset: dict | None) -> dict:
    parts = {side: inventory(texts[side]) for side in ('a', 'b')}
    status = {'a': None, 'b': (typeset or {}).get('status')}
    rows = [{'key': key, **{side: parts[side][key] for side in ('a', 'b')}} for key in ('notes', 'glossary', 'persons')]
    rows += [{'key': 'typeset', **status}, {'key': 'edits', **done_edits}]
    checks = {side: sum(bool(parts[side][key]) for key in CHECKS[:3]) + (status[side] == 'done')
              for side in ('a', 'b')}
    return {'rows': rows, 'checks': checks, 'total': len(CHECKS), 'in_total': False,
            'download': (typeset or {}).get('url') if status['b'] == 'done' else None}
