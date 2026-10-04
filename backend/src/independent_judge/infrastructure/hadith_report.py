"""Portable source evidence with explicit matching limits."""
from html import escape

LABELS = {'exact': 'Полное совпадение', 'normalized': 'Совпадение без огласовок',
          'fragment': 'Совпадает фрагмент', 'review': 'Есть расхождения — нужна проверка',
          'ambiguous': 'Несколько соответствий', 'not_found': 'Не найдено в подключённых сборниках',
          'unavailable': 'Источник недоступен'}


def _record(record):
    e = lambda x: escape(str(x), quote=True)
    return (f'<a href="{e(record["url"])}">{e(record["url"])}</a>'
            f'<blockquote dir="auto">{e(record["text"])}</blockquote>'
            f'<blockquote>{e(record.get("english_text", ""))}</blockquote>'
            f'<p>{e(record.get("grade", ""))}</p>'
            f'<p>Получено: {e(record["retrieved_at"])}; SHA-256: {e(record["snapshot_sha256"])}</p>')


def hadith_html(result):
    if not result: return '<h2>Хадисы</h2><p>Библиотечная сверка ещё не выполнена.</p>'
    content = '<h2>Хадисы и источники</h2><p>Текстовое соответствие не является заключением о достоверности или точности перевода.</p>'
    content += f'<p>Состояние: {escape(result["status"])}. {escape(result.get("library", ""))}</p>'
    for item in result['items']:
        content += f'<h3>{LABELS[item["status"]]}</h3><blockquote dir="auto">{escape(item["quote"])}</blockquote>'
        content += ''.join(_record(c) for c in item['candidates'])
    official = result.get('official')
    if official:
        content += '<h3>Sunnah.com</h3>'
        if official['status'] == 'requires_key': content += '<p>Официальная сверка ожидает API-доступ.</p>'
        if official.get('limit_reached'): content += '<p>Sunnah.com: лимит 10 записей, часть соответствий не проверена.</p>'
        for check in official['records']:
            content += f'<h4>{LABELS[check["status"]]}</h4>'
            if check['record']: content += _record(check['record'])
    return content
