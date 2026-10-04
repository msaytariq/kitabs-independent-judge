"""Validate declared semantic boundaries by exact coordinates, not length ratios.

The caller reviews that boundary quotes refer to the same source passage.
This deterministic check proves preservation and placement, not translation quality.
"""
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash


def verify_boundary_selection(full_texts: dict, selections: dict) -> dict:
    texts, ranges = {}, {}
    for role in ('source', 'a', 'b'):
        full, selected = full_texts[role], selections[role]
        start, end = selected['start'], selected['end']
        if text_hash(full) != selected['input_sha256']:
            raise InputError('stale_input', 'Полный исходник изменился.')
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(full):
            raise InputError('invalid_boundary', 'Граница выходит за пределы исходника.')
        text = full[start:end]
        if (not selected['start_quote'] or not selected['end_quote']
                or not text.startswith(selected['start_quote']) or not text.endswith(selected['end_quote'])):
            raise InputError('boundary_quote_mismatch', 'Граничные цитаты не совпадают с выбранным фрагментом.')
        texts[role] = text
        ranges[role] = {'start': start, 'end': end, 'text_sha256': selected['input_sha256']}
    return {'texts': texts, 'ranges': ranges, 'hashes': {k: text_hash(v) for k, v in texts.items()}}
