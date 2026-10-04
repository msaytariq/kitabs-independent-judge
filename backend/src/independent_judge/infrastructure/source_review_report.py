"""Escaped HTML presentation of a validated source review, separate from judge scores."""
from html import escape


def source_review_html(review: dict | None) -> str:
    if not review:
        return ''
    e = lambda value: escape(str(value))
    evidence = {item['id']: item for item in review['evidence']}
    sources = {item['id']: item for item in review['sources']}

    def proof(item):
        quotes = ''.join(f'<p>{e(evidence[key]["label_ru"])}</p><blockquote dir="auto">'
                         f'{e(evidence[key]["text"])}</blockquote>' for key in item['evidence_ids'])
        refs = ''.join(f'<li><a href="{e(sources[key]["url"])}">{e(sources[key]["label"])}</a></li>'
                       for key in item.get('source_ids', []))
        return f'<details><summary>Цитаты и источники</summary>{quotes}<ul>{refs}</ul></details>'

    benefits = ''.join(f'<article><h3>{e(item["title_ru"])}</h3><p>{e(item["detail_ru"])}</p>{proof(item)}</article>'
                       for item in review['benefits'])
    checks = ''.join(f'<article><h3>{e(item["title_ru"])}</h3><p><b>A:</b> {e(item["a_ru"])}</p>'
                     f'<p><b>B — Kitabs:</b> {e(item["b_ru"])}</p><p>{e(item["conclusion_ru"])}</p>{proof(item)}</article>'
                     for item in review['checks'])
    tasks = ''.join(f'<article><h3>{"Обе стороны" if item["side"] == "both" else "Перевод " + item["side"].upper()}: '
                    f'{e(item["title_ru"])}</h3><p>{e(item["reason_ru"])}</p>'
                    + (f'<details><summary>Проект дополнения — не применён</summary><p>{e(item["draft_ru"])}</p></details>'
                       if item.get('draft_ru') else '') + proof(item) + '</article>' for item in review['tasks'])
    refs = ''.join(f'<li><a href="{e(s["url"])}">{e(s["label"])}</a><p>{e(s["summary_ru"])}</p></li>'
                   for s in review['sources'])
    limits = ''.join(f'<li>{e(value)}</li>' for value in review['limitations_ru'])
    return f'''<section><h2>Разбор по источникам</h2>
    <p>Подготовил Codex · {e(review['checked_on'])} · без нового прогона судьи</p>
    <p>{e(review['summary_ru'])}</p><h3>Что уже сделала платформа</h3>{benefits}
    <h3>Сопоставление A и B</h3>{checks}<h3>Работа редактора</h3>
    <p>Это конкретные задачи для проверки и дополнения, а не окончательный счёт ошибок.</p>{tasks}
    <details><summary>Проверенные источники и границы разбора</summary><ul>{refs}</ul><ul>{limits}</ul></details></section>'''
