"""Self-contained Russian HTML export of the same comparison projection."""
from html import escape
from independent_judge.infrastructure.apparatus_report import apparatus_html
from independent_judge.infrastructure.source_review_report import source_review_html
from independent_judge.infrastructure.effort_report import effort_html
from independent_judge.infrastructure.hadith_report import hadith_html
from independent_judge.infrastructure.rubric_report import rubric_html, processing_html

LABELS = {'K': 'Критические', 'T': 'Терминология', 'A': 'Научный аппарат', 'S': 'Стиль', '?': 'Категория спорная'}


def _locations(anchors: dict) -> str:
    return '; '.join(('оригинал' if role == 'source' else 'перевод') + ': ' +
                     (', '.join(f'{r["start"]}–{r["end"]}' for r in a['ranges']) or 'не найдено')
                     for role, a in anchors.items())


def comparison_html(view: dict) -> str:
    e = lambda value: escape(str(value))
    summary, scope = view['summary'], view['scope']
    rows = ''.join('<tr><th>' + label + '</th>' + ''.join(
        '<td>' + (str(summary['sides'][s]['by_code'][code])
                   if summary['sides'][s]['by_code'] is not None else 'не оценено') + '</td>'
        for s in ('a', 'b')) + '</tr>' for code, label in LABELS.items() if code != '?')
    findings = ''.join(f'''<article><h3>Перевод {f['side'].upper()} · {LABELS[f['code']]}</h3>
        <p>{'Спорное замечание' if f['status'] == 'disputed' else 'Цитата не найдена однозначно' if f['status'] == 'unlocated' else 'Требует проверки'}</p>
        <p>Оригинал</p><blockquote dir="auto">{e(f['source_excerpt'])}</blockquote>
        <p>В переводе</p><blockquote dir="auto">{e(f['current_text'])}</blockquote>
        <p>{e(f.get('why_ru') or f['why'])}</p><p>{e(f.get('review_note_ru') or '')}</p>
        <details><summary>Сохранённый ответ модели</summary><p>{e(f['why'])}</p>
        <p>Предложение модели: {e(f['should_be'])}</p></details>
        <p>Места в выборке (с нуля, конец не включён): {e(_locations(f['anchors']))}</p></article>'''
        for f in summary['findings'])
    materials = ''.join(f'<h3>{label}</h3><pre dir="auto">{e(scope["texts"][role])}</pre>'
                         for role, label in [('source', 'Оригинал'), ('a', 'Перевод A'), ('b', 'Перевод B')])
    notes = ''.join(f'<h3>Перевод {side.upper()}</h3>' + ''.join(
        f'<p>[{e(n["number"])}] {e(n["text"])}</p>' for n in (view.get('apparatus') or {}).get(side, []))
        for side in ('a', 'b'))
    boundary = (view.get('boundary_review') or {}).get('note_ru', 'Границы заданы при подготовке материалов.')
    provenance = view.get('provenance') or {}
    run = view.get('run')
    passport = ''.join(f'<p>{label}: {e(provenance.get(key, "не указано"))}</p>'
                       for key, label in [('book', 'Произведение'), ('a', 'Перевод A'), ('b', 'Перевод B')])
    if run:
        passport += f'<p>Прогон: <code>{e(run["id"])}</code>. Судья: {e(run["model"])}.</p>'
        passport += f'<p>{e(provenance.get("independence_note", "Независимость судьи от переводчиков отдельно не подтверждена."))}</p>'
    passport += ''.join(f'<p>Хэш {label}: <code>{e(scope["hashes"][role])}</code></p>'
                        for role, label in [('source','оригинала'),('a','перевода A'),('b','перевода B')])
    rubric_mode = bool(view.get('rubric') or view.get('rubric_protocol'))
    candidates = ''.join(f'<p>Перевод {side.upper()}: находок — {s["candidates"] if s["candidates"] is not None else "не оценено"}; '
                         f'спорных — {s["disputed"]}. Необходимых правок: не установлено.</p>'
                         for side, s in summary['sides'].items())
    legacy = f'''<p>{'Машинная оценка сохранена в отчёте.' if summary['measured'] else 'Завершённой ИИ-оценки нет.'}</p>
    {candidates}<table><tr><th>Кандидаты на проверку, включая спорные</th><th>A</th><th>B</th></tr>{rows}</table>
    <p>Повторные проходы не суммируются. Совпадающие пары цитат считаются один раз. Машинные находки не являются подтверждёнными ошибками; сложность правок и экономия времени не измерены.</p>
    <h2>Обоснования</h2><p>Русские пояснения подготовлены Codex по сохранённым ответам. Это не заключение независимого эксперта.</p>{findings or '<p>Нет находок для отображения; это не подтверждение безошибочности.</p>'}'''
    return f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
    <title>Независимый судья — {e(view['title'])}</title><style>
    body{{max-width:1000px;margin:40px auto;padding:0 24px;font:16px/1.6 Arial;color:#182f39}}
    table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border:1px solid #ccd7d1;text-align:left}}
    pre,blockquote{{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#f4f6f1;padding:16px}}
    article{{border-top:1px solid #ccd7d1;padding:14px 0}}code{{overflow-wrap:anywhere}}
    @media print{{body{{margin:0}}details{{display:block}}}}</style>
    <h1>Независимый судья</h1><h2>{e(view['title'])}</h2><p>{e(view.get('description') or '')}</p>
    {rubric_html(view.get('rubric'), view.get('rubric_protocol', False)) + processing_html(view['processing_effort']) if rubric_mode else ''}
    {apparatus_html(view.get('generated_apparatus'))}
    {'' if rubric_mode else effort_html(view['effort'])}
    {hadith_html(view.get('hadith'))}
    {source_review_html(view.get('source_review'))}
    {'' if rubric_mode else '<p>Необходимых правок: <b>не установлено</b>. Экспертная проверка не завершена.</p>'}
    <p>Оригинал: {summary['source_chars']} знаков, {summary['source_pages']} условной страницы по 1800 знаков.</p>
    <p>{'Выборка меньше 3 страниц: обобщать результат на книгу или платформу нельзя.' if not summary['negotiation_grade'] else ''}</p>
    {'' if rubric_mode else legacy}
    <h2>Научный аппарат</h2><p>Сохранённые примечания. Наличие сносок не подтверждает их правильность. Потребность в дополнении и исправлении отдельно не установлена.</p>{notes}
    <h2>Границы фрагмента</h2><p>{e(boundary)}</p>
    <h2>Материалы полностью</h2>{materials}
    <h2>Паспорт</h2>{passport}
    <p>Полная проверка справочников Корана и хадисов в этом стенде не выполнялась.</p>
    </html>'''
