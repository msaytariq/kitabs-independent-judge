"""Russian HTML sections for the rubric table and measured processing time."""
from html import escape

CRITERIA = {'accuracy': 'Точность', 'completeness': 'Полнота', 'terminology': 'Терминология',
            'readability': 'Читаемость', 'seamlessness': 'Целостность сборки', 'apparatus': 'Научный аппарат'}
WINNERS = {'a': 'Лучше перевод A', 'b': 'Лучше перевод B', 'tie': 'Переводы равны'}
TIME_ROWS = [('pipeline_seconds', 'Пайплайн, секунды'), ('audit_operations', 'Применённые правки аудита'),
             ('editor_operations', 'Применённые правки редактора'),
             ('simulated_seconds', 'Смоделированное принятие, секунды'), ('total_seconds', 'Итого, секунды')]


LEGEND = ('100 — замечаний нет; 75 — мелкие местные дефекты; 50 — заметные дефекты; '
          '25 — много существенных ошибок; 0 — смысл систематически искажён.')
COVERAGE_LABELS = {'quran': 'Аяты Корана в переводе', 'hadith': 'Хадисы в переводе'}


def _cell(side: dict, value: int | None) -> str:
    e = lambda text: escape(str(text))
    if value is None:
        return '<td>—</td>'
    evidence = ''.join(f'''<p>Оригинал</p><blockquote dir="auto">{e(x["source_quote"])}</blockquote>
        <p>Перевод</p><blockquote dir="auto">{e(x["translation_quote"])}</blockquote><p>{e(x["explanation_ru"])}</p>'''
        for x in side['evidence'])
    return (f'<td><b>{value}</b><br>уровень {side["score"]} из 5<details><summary>Почему</summary>'
            f'<p>{e(side["explanation_ru"])}</p>{evidence}</details></td>')


def _effort_html(effort: dict | None) -> str:
    if not effort:
        return ''
    rows = [('Осталось правок', 'edits'), ('из них ошибки с цитатами', 'defects'),
            ('из них пропущенные аяты и хадисы', 'missing_quotations'),
            ('Принятие правок Kitabs, минуты', 'review_minutes'), ('Время редактора, минуты', 'minutes')]
    body = ''.join(f'<tr><th>{label}</th><td>{effort["a"][key]}</td><td>{effort["b"][key]}</td></tr>' for label, key in rows)
    percent = effort['reduction_percent']
    a, b = effort['a']['minutes'], effort['b']['minutes']
    if a > b and percent is not None:
        verdict = f'<p><b>Экономия времени с B: {percent}%</b></p>'
    elif a < b:
        verdict = f'<p><b>A требует меньше редактуры: {a} против {b} минут</b></p>'
    else:
        verdict = '<p><b>Время редактуры одинаково</b></p>'
    return (f'<section><h2>Редактура до публикации</h2><table><tr><th>Показатель</th><th>A</th><th>B</th></tr>{body}</table>'
            f'{verdict}<p>Допущение: {effort["minutes_per_edit"]} минуты на одну правку редактора; '
            '5 секунд на принятие одной правки, которую Kitabs уже применил.</p></section>')


def _case_html(study: dict | None) -> str:
    if not study:
        return ''
    e = lambda text: escape(str(text))
    body = ''
    for side in ('a', 'b'):
        if not study[side]:
            body += f'<p>В {side.upper()} ошибок с цитатами нет.</p>'
        for d in study[side]:
            body += (f'<article><h3>Перевод {side.upper()} · {CRITERIA.get(d["criterion"], e(d["criterion"])).lower()}</h3>'
                     f'<p>Оригинал</p><blockquote dir="auto">{e(d["source_quote"])}</blockquote>'
                     f'<p>Перевод</p><blockquote dir="auto">{e(d["translation_quote"])}</blockquote>'
                     f'<p>{e(d["explanation_ru"])}</p></article>')
    if study['kitabs_corrections']:
        body += '<h3>Что исправил аудит Kitabs на пути к B</h3>' + ''.join(
            f'<p><del>{e(c["before"])}</del></p><p><ins>{e(c["after"])}</ins></p>' for c in study['kitabs_corrections'])
    return f'<section><h2>Что поймал судья</h2>{body}</section>'


def rubric_html(view: dict) -> str:
    rubric, jury = view.get('rubric'), view.get('jury')
    if not rubric or not jury:
        reason = 'Оценка не завершена.' if view.get('rubric_protocol') else 'Запустите сравнение, чтобы получить оценку.'
        return f'<section><h2>{reason}</h2></section>'
    indexed = {r['criterion']: r for r in rubric['criteria']}
    rows = ''
    for row in jury['rows']:
        if row['kind'] == 'criterion':
            source = indexed[row['key']]
            rows += (f'<tr><th>{CRITERIA.get(row["key"], escape(row["key"]))}</th>'
                     f'{_cell(source["a"], row["a"])}{_cell(source["b"], row["b"])}</tr>')
        else:
            rows += (f'<tr><th>{COVERAGE_LABELS[row["key"]]}</th>' + ''.join(
                f'<td><b>{row[s]}</b><br>{row["found"][s]} из {row["total"]}</td>' for s in ('a', 'b')) + '</tr>')
    total = ''.join(f'<td><b>{jury["totals"][s]}</b></td>' if jury['totals'][s] is not None else '<td>—</td>'
                    for s in ('a', 'b'))
    summary = ''.join(f'<li>{escape(line)}</li>' for line in (view.get('jury_summary') or {}).get('ru', []))
    defects = rubric['unique_defects']
    return f'''<section><h2>{WINNERS.get(jury['winner'], 'Оценка не завершена.')}</h2>
    <table><tr><th>Показатель, баллы 0–100</th><th>A</th><th>B</th></tr>{rows}<tr><th>Итог, 0–100</th>{total}</tr></table>
    <ul>{summary}</ul>
    <p>Ошибки с цитатами: A — {defects['a']}; B — {defects['b']}.</p>
    <p>{LEGEND}</p>
    <p>ИИ-судья выставляет уровни 1–5 по одинаковым критериям для A и B: 1 = 0, 2 = 25, 3 = 50, 4 = 75, 5 = 100 баллов.
    Строки аятов и хадисов — доля цитат оригинала, найденных в переводе. Итог — среднее всех строк.</p></section>''' + _case_html(view.get('case_study')) + _effort_html(view.get('effort_reduction'))


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
