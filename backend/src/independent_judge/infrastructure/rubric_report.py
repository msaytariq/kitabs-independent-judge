"""Russian HTML sections for the rubric table and measured processing time."""
from html import escape

CRITERIA = {'accuracy': 'Точность', 'completeness': 'Полнота', 'terminology': 'Терминология',
            'readability': 'Читаемость', 'seamlessness': 'Целостность сборки', 'apparatus': 'Научный аппарат'}
WINNERS = {'a': 'Лучше перевод A', 'b': 'Лучше перевод B', 'tie': 'Переводы равны'}
TIME_ROWS = [('pipeline_seconds', 'Пайплайн, секунды'), ('audit_operations', 'Применённые правки аудита'),
             ('editor_operations', 'Применённые правки редактора'),
             ('simulated_seconds', 'Смоделированное принятие, секунды'), ('total_seconds', 'Итого, секунды')]


def _number(value: float) -> str:
    return f'{value:.1f}'.replace('.', ',')


def _cell(side: dict) -> str:
    e = lambda value: escape(str(value))
    value = f'{side["score"]} / 5' if side['score'] is not None else '—'
    evidence = ''.join(f'''<p>Оригинал</p><blockquote dir="auto">{e(x["source_quote"])}</blockquote>
        <p>Перевод</p><blockquote dir="auto">{e(x["translation_quote"])}</blockquote><p>{e(x["explanation_ru"])}</p>'''
        for x in side['evidence'])
    return (f'<td><b>{value}</b><details><summary>Почему</summary>'
            f'<p>{e(side["explanation_ru"])}</p>{evidence}</details></td>')


def rubric_html(rubric: dict | None, rubric_protocol: bool) -> str:
    if not rubric:
        reason = 'Оценка не завершена.' if rubric_protocol else 'Запустите сравнение, чтобы получить оценку.'
        return f'<section><h2>{reason}</h2></section>'
    rows = ''.join(f'<tr><th>{CRITERIA.get(r["criterion"], escape(r["criterion"]))}</th>'
                   f'{_cell(r["a"])}{_cell(r["b"])}</tr>' for r in rubric['criteria'])
    totals = rubric['totals']
    total = ''.join(f'<td><b>{_number(totals[s])} / 5</b></td>' if totals[s] is not None else '<td>—</td>'
                    for s in ('a', 'b'))
    defects = rubric['unique_defects']
    return f'''<section><h2>{WINNERS.get(rubric['winner'], 'Оценка не завершена.')}</h2>
    <table><tr><th>Критерий</th><th>A</th><th>B</th></tr>{rows}<tr><th>Итог</th>{total}</tr></table>
    <p>Ошибки с цитатами: A — {defects['a']}; B — {defects['b']}.</p>
    <p>Оценки 1–5 выставляет ИИ-судья по одинаковым критериям для A и B. Итог — среднее оценок по критериям.</p></section>'''


def processing_html(effort: dict) -> str:
    def unknown(key):
        return 'Время не установлено' if key == 'total_seconds' else '—'
    rows = ''.join(f'<tr><th>{label}</th>' + ''.join(
        f'<td>{round(effort["sides"][s][key]) if effort["sides"][s][key] is not None else unknown(key)}</td>'
        for s in ('a', 'b')) + '</tr>' for key, label in TIME_ROWS)
    edits = ''.join(f'<details><summary>{side.upper()} · Применённые правки: до / после</summary>' + ''.join(
        f'<p>{"Аудит" if op["stage"] == "audit" else "Редактор"} · {escape(op["chunk_id"])}</p>'
        f'<p><del>{escape(op["before"])}</del></p><p><ins>{escape(op["after"])}</ins></p>'
        for op in s['operations']) + '</details>' for side, s in effort['sides'].items() if s['operations'])
    return f'''<section><h2>Время обработки</h2><table><tr><th>Показатель</th><th>A</th><th>B</th></tr>{rows}</table>
    <p>Правки приняты автоматически. Участие человека смоделировано: 5 секунд на принятие одной применённой
    правки аудита или редактора. Корректор входит во время пайплайна.</p>{edits}</section>'''
