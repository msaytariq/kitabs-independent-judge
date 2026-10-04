"""Validate a saved desk review against immutable candidate evidence, without scoring."""
from urllib.parse import urlsplit

from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash


def _require(condition: bool) -> None:
    if not condition:
        raise InputError('invalid_source_review', 'Разбор не соответствует исходным текстам, примечаниям или ссылкам.')


def _unique(items: list) -> set[str]:
    ids = [item['id'] for item in items]
    _require(all(isinstance(value, str) and value for value in ids) and len(ids) == len(set(ids)))
    return set(ids)


def _evidence_text(item: dict, record: dict) -> tuple[str, str]:
    role = item['role']
    if role in ('source', 'a', 'b'):
        return record['scope']['texts'][role], {'source': 'Оригинал', 'a': 'Перевод A', 'b': 'Перевод B'}[role]
    if role in ('note_a', 'note_b'):
        notes = [n for n in record['apparatus'][role[-1]] if n['number'] == item['number']]
        _require(len(notes) == 1)
        return notes[0]['text'], f'Примечание {role[-1].upper()} [{item["number"]}]'
    _require(role == 'artifact_b')
    artifact = record['capability_evidence']
    text = artifact['artifact_text']
    _require(text_hash(text) == artifact['artifact_sha256'] == item['artifact_sha256'])
    _require(artifact['scope_hashes'] == record['scope']['hashes'])
    selection = artifact['translation_range']
    _require(text[selection['start']:selection['end']] == record['scope']['texts']['b'])
    return text, 'Полный сохранённый результат Kitabs'


def source_review(record: dict) -> dict | None:
    review = record.get('source_review')
    if review is None:
        return None
    try:
        _require(review['version'] == 1)
        actual = {role: text_hash(value) for role, value in record['scope']['texts'].items()}
        _require(review['scope_hashes'] == record['scope']['hashes'] == actual)
        notes = {side: [{'number': n['number'], 'sha256': text_hash(n['text'])}
                        for n in record['apparatus'][side]] for side in ('a', 'b')}
        _require(review['apparatus_hashes'] == notes)
        evidence_ids, source_ids = _unique(review['evidence']), _unique(review['sources'])
        evidence = []
        for item in review['evidence']:
            text, label = _evidence_text(item, record)
            start, end = item['start'], item['end']
            _require(type(start) is int and type(end) is int and 0 <= start < end <= len(text))
            _require(text[start:end] == item['text'] and text_hash(item['text']) == item['sha256'])
            evidence.append(item | {'label_ru': label})
        for source in review['sources']:
            url = urlsplit(source['url'])
            _require(url.scheme == 'https' and bool(url.hostname) and not url.username and not url.password)
            _require(all(isinstance(source[key], str) for key in ('label', 'summary_ru')))
        for section in ('benefits', 'checks', 'tasks'):
            if section != 'benefits':
                _unique(review[section])
            for item in review[section]:
                _require(bool(item['evidence_ids']) and set(item['evidence_ids']) <= evidence_ids)
                _require(set(item.get('source_ids', [])) <= source_ids)
                fields = {'benefits': ('title_ru', 'detail_ru'),
                          'checks': ('title_ru', 'a_ru', 'b_ru', 'conclusion_ru'),
                          'tasks': ('title_ru', 'reason_ru')}[section]
                _require(all(isinstance(item[key], str) for key in fields))
                if section == 'tasks':
                    _require(item['side'] in ('a', 'b', 'both'))
                    _require(isinstance(item.get('draft_ru', ''), str))
        _require(all(isinstance(review[key], str) for key in ('id', 'checked_on', 'summary_ru')))
        _require(isinstance(review['limitations_ru'], list) and
                 all(isinstance(value, str) for value in review['limitations_ru']))
        return {key: review[key] for key in ('version', 'id', 'checked_on', 'summary_ru', 'sources',
                                             'benefits', 'checks', 'tasks', 'limitations_ru')} | {
            'status': 'desk_review', 'evidence': evidence}
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError('invalid_source_review', 'Файл разбора повреждён.') from exc
