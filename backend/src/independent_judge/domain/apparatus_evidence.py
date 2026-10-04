"""Prove the presence of generated apparatus from exact immutable output spans."""
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash


def _slice(text: str, selection: dict) -> str:
    start, end = selection['start'], selection['end']
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
        raise InputError('invalid_apparatus_range', 'Неверный диапазон научного аппарата.')
    return text[start:end]


def apparatus_evidence(evidence: dict | None, scope: dict) -> dict | None:
    if evidence is None: return None
    text = evidence['artifact_text']
    if (text_hash(text) != evidence['artifact_sha256'] or evidence['scope_hashes'] != scope['hashes']
            or _slice(text, evidence['translation_range']) != scope['texts']['b']):
        raise InputError('stale_apparatus', 'Аппарат не связан с этим сохранённым результатом.')
    seen, ids, groups = [], set(), []
    for group in evidence['groups']:
        if group['id'] in ids:
            raise InputError('duplicate_apparatus_group', 'Раздел аппарата повторяется.')
        ids.add(group['id'])
        for item in group['items']:
            if _slice(text, item) != item['text'] or text_hash(item['text']) != item['sha256']:
                raise InputError('stale_apparatus_quote', 'Цитата аппарата изменена.')
            if any(item['start'] < end and start < item['end'] for start, end in seen):
                raise InputError('duplicate_apparatus_item', 'Пересекающиеся записи нельзя считать дважды.')
            seen.append((item['start'], item['end']))
        indices = group['sample_indices']
        if any(type(i) is not int or not 0 <= i < len(group['items']) for i in indices):
            raise InputError('invalid_apparatus_example', 'Пример не найден в разделе.')
        groups.append({key: group[key] for key in ('id', 'title_ru', 'purpose_ru')} | {
            'count': len(group['items']), 'examples': [group['items'][i] for i in indices]})
    return {key: evidence[key] for key in ('artifact_sha256', 'label_ru', 'scope_label_ru')} | {
        'groups': groups, 'quality_status': 'not_adjudicated'}
