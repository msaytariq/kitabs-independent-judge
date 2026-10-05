"""Russian HTML sections for the paired rubric and measured processing time."""
from html import escape

CRITERIA = {'accuracy': 'Точность', 'completeness': 'Полнота', 'terminology': 'Терминология',
            'readability': 'Читаемость', 'seamlessness': 'Целостность сборки', 'apparatus': 'Научный аппарат'}
STATES = {'not_assessed': 'Не оценено', 'not_applicable': 'Не применимо', 'unstable': 'Неустойчиво',
          'unverified_evidence': 'Цитата не подтверждена'}
VERDICTS = {'a': 'На этом материале преимущество у A', 'b': 'На этом материале преимущество у B',
            'mixed': 'Преимущества по разным критериям', 'none': 'Устойчивое преимущество не установлено'}
TIME_ROWS = [('pipeline_seconds', 'Пайплайн, секунды'), ('audit_operations', 'Применённые правки аудита'),
             ('editor_operations', 'Применённые правки редактора'),
             ('simulated_seconds', 'Смоделированное принятие, секунды'), ('total_seconds', 'Итого, секунды')]


def _cell(side: dict) -> str:
    e = lambda value: escape(str(value))
    value = f'{side["score"]} / 5' if side['score'] is not None else STATES.get(side['status'], 'Не оценено')
    notes = ''
    if side['status'] == 'unstable':
        notes += '<p>Проходы: ' + ' / '.join('—' if v is None else str(v) for v in side['pass_scores']) + '</p>'
    if side.get('evidence_conflict'):
        notes += '<p>Проходы пришли к противоположным выводам по одной и той же цитате.</p>'
    explanations = ''.join(f'<p>{e(x["explanation_ru"])}</p>' for x in side['explanations'])
    evidence = ''.join(f'''<p>Оригинал</p><blockquote dir="auto">{e(x["source_quote"])}</blockquote>
        <p>Перевод</p><blockquote dir="auto">{e(x["translation_quote"])}</blockquote><p>{e(x["explanation_ru"])}</p>
        <p>{'Точная цитата найдена; вывод сделан машиной.' if x['verified'] else 'Цитата не найдена или неоднозначна.'}</p>'''
        for x in side['evidence'])
    return (f'<td><b>{e(value)}</b>{notes}<details><summary>Доказательства и охват</summary>'
            f'{explanations}{evidence}</details></td>')


def paired_html(paired: dict | None, paired_protocol: bool) -> str:
    if not paired:
        reason = ('Запуск по парной методике не завершён; оценки не выставлены.' if paired_protocol
                  else 'Запустите сравнение для получения машинных оценок.')
        return f'<section><h2>По парной методике не оценено</h2><p>{reason}</p></section>'
    rows = ''.join(f'<tr><th>{CRITERIA.get(r["criterion"], escape(r["criterion"]))}</th>'
                   f'{_cell(r["a"])}{_cell(r["b"])}</tr>' for r in paired['criteria'])
    defects = paired['unique_defects']
    return f'''<section><h2>{VERDICTS.get(paired['advantage'], VERDICTS['none'])}</h2>
    <p>Машинная оценка · 1–5 · только выбранный материал. Общий балл не рассчитывается.</p>
    <table><tr><th>Критерий</th><th>A</th><th>B</th></tr>{rows}</table>
    <p>Уникальные привязанные кандидаты на ошибки: A — {defects['a']}; B — {defects['b']}.
    Количество не показывает, во сколько раз перевод качественнее.</p>
    <p>Оригинал и два анонимных перевода, затем сравнение в обратном порядке. Два прохода одной модели
    не являются независимой панелью.</p></section>'''


def processing_html(effort: dict) -> str:
    unknown = 'Время не установлено'
    rows = ''.join(f'<tr><th>{label}</th>' + ''.join(
        f'<td>{escape(str(effort["sides"][s][key])) if effort["sides"][s][key] is not None else unknown}</td>'
        for s in ('a', 'b')) + '</tr>' for key, label in TIME_ROWS)
    edits = ''.join(f'<details><summary>{side.upper()} · Применённые правки: до / после</summary>' + ''.join(
        f'<p>{"Аудит" if op["stage"] == "audit" else "Редактор"} · {escape(op["chunk_id"])}</p>'
        f'<p><del>{escape(op["before"])}</del></p><p><ins>{escape(op["after"])}</ins></p>'
        for op in s['operations']) + '</details>' for side, s in effort['sides'].items() if s['operations'])
    return f'''<section><h2>Время обработки</h2><table><tr><th>Показатель</th><th>A</th><th>B</th></tr>{rows}</table>
    <p>Правки приняты автоматически. Участие человека смоделировано: 5 секунд на принятие одной применённой
    правки аудита или редактора. Корректор входит во время пайплайна.</p>
    <p>Это не измерение исследования источников и не гарантия безошибочного текста.
    Замечания судьи не входят в расчёт времени.</p>{edits}</section>'''
