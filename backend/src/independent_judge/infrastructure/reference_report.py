"""Portable summary of Quran verses and hadith found in the original."""
from html import escape

STATES = {'exact': 'Точное совпадение', 'normalized': 'Совпадение без огласовок',
          'fragment': 'Цитата — часть хадиса', 'ambiguous': 'Найден в нескольких сборниках',
          'review': 'Близкий текст с расхождениями', 'not_found': 'Нет в подключённых сборниках'}


def reference_html(result) -> str:
    if not result or result.get('status') != 'checked' or not result.get('quran'):
        return '<h2>Источники в оригинале</h2><p>Сверка источников ещё не выполнена.</p>'
    e = lambda value: escape(str(value), quote=True)
    quran, hadith = result['quran'], result['hadith']
    content = '<h2>Источники в оригинале</h2>'
    content += f'<p><b>Аяты Корана: найдено {quran["found"]} из {quran["total"]}</b></p>'
    wrong = [item for item in quran['items'] if item.get('label_status') == 'label_differs']
    if wrong:
        content += ('<p>Издание печатает эти ссылки с ошибкой. Код нашёл каждый аят по тексту и указывает '
                    'его настоящее место в Коране.</p>')
    for item in wrong:
        content += f'<p>В издании напечатано: «{e(item["label"])}» — в Коране: {e(item["ayah"])}</p>'
    collections = ', '.join(f'{e(name)} — {n}' for name, n in hadith['by_collection'].items())
    content += f'<p><b>Хадисы: найдено {hadith["found"]} из {hadith["total"]}</b>{" · " + collections if collections else ""}</p>'
    content += '<details><summary>Аяты и хадисы по отдельности</summary>'
    for item in quran['items']:
        where = f'Коран {e(item["ayah"])} · {e(item["surah_name"])}' if item['status'] == 'found' else 'Не найдено в тексте Корана'
        content += f'<blockquote dir="auto">{e(item["quote"])}</blockquote><p>{where}</p>'
    for item in hadith['items']:
        links = ''.join(f'<a href="{e(c["url"])}">{e(c["collection"])} {e(c["number"])}</a> ' for c in item['candidates'])
        content += f'<blockquote dir="auto">{e(item["quote"])}</blockquote><p>{STATES.get(item["status"], e(item["status"]))} {links}</p>'
    content += ('<p>Тексты: открытый текст Корана и арабские издания Бухари, Муслима, Абу Дауда, Тирмизи, Насаи, '
                'Ибн Маджи и Малика. Совпадение текста не является заключением о достоверности.</p></details>')
    official = result.get('official') or {}
    if official.get('status') not in (None, 'requires_key'):
        content += '<h3>Sunnah.com</h3>'
        for check in official.get('records', []):
            content += f'<p>{STATES.get(check["status"], e(check["status"]))}</p>'
            record = check.get('record')
            if record:
                content += (f'<a href="{e(record["url"])}">{e(record["url"])}</a>'
                            f'<blockquote dir="auto">{e(record["text"])}</blockquote>'
                            f'<p>{e(record.get("grade", ""))}</p>')
    return content
