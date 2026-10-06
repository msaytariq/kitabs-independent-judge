"""Points 0-100, remaining editing work and a plain summary for the jury table.

The judge grades levels 1-5; each level has a written definition (paired_rubric.RUBRIC).
Points only rename the levels: 1 -> 0, 2 -> 25, 3 -> 50, 4 -> 75, 5 -> 100.
"""
import math
from independent_judge.domain.paired_rubric import RUBRIC

VERSION = 'points-v1'
EFFORT_VERSION = 'effort-v2'
MINUTES_PER_EDIT = 3
COVERAGE_KEYS = ('quran', 'hadith')
LABELS = {
    'en': {'accuracy': 'accuracy', 'completeness': 'completeness', 'terminology': 'terminology',
           'readability': 'readability', 'seamlessness': 'seamless assembly',
           'apparatus': 'scholarly apparatus', 'quran': 'Quran verses', 'hadith': 'hadith',
           'takhrij': 'hadith takhrij', 'verse_refs': 'verse references', 'editing': 'editing', 'seams': 'seams without breaks',
           'critical': 'critical errors'},
    'ru': {'accuracy': 'точность', 'completeness': 'полнота', 'terminology': 'терминология',
           'readability': 'читаемость', 'seamlessness': 'бесшовность сборки',
           'apparatus': 'научный аппарат', 'quran': 'аяты Корана', 'hadith': 'хадисы',
           'takhrij': 'тахридж хадисов', 'verse_refs': 'ссылки на аяты', 'editing': 'редактура', 'seams': 'стыки без разрывов',
           'critical': 'критические ошибки'},
    'ar': {'accuracy': 'الدقة', 'completeness': 'الاكتمال', 'terminology': 'المصطلحات',
           'readability': 'سهولة القراءة', 'seamlessness': 'تجميع بلا فواصل',
           'apparatus': 'الجهاز العلمي', 'quran': 'آيات القرآن', 'hadith': 'الأحاديث',
           'takhrij': 'تخريج الأحاديث', 'verse_refs': 'الإحالات إلى الآيات', 'editing': 'التحرير', 'seams': 'وصلات بلا انقطاع',
           'critical': 'الأخطاء الجسيمة'},
}
PHRASES = {
    'en': {'tie': 'The translations are equal: {a} points each.',
           'win': 'Translation {win} is better: {high} against {low} points.',
           'better': '{side} is better in: ', 'equal': 'Equal in: ', 'comma': ', ',
           'critical': 'Critical errors: A — {a}, B — {b}.'},
    'ru': {'tie': 'Переводы равны: итог {a} из 100 у каждого.',
           'win': 'Перевод {win} лучше: {high} против {low} баллов.',
           'better': '{side} лучше в: ', 'equal': 'Одинаково: ', 'comma': ', ',
           'critical': 'Критические ошибки: A — {a}, B — {b}.'},
    'ar': {'tie': 'الترجمتان متساويتان: {a} نقطة لكل منهما.',
           'win': 'الترجمة {win} أفضل: {high} مقابل {low} نقطة.',
           'better': '{side} أفضل في: ', 'equal': 'متساويتان في: ', 'comma': '، ',
           'critical': 'الأخطاء الجسيمة: A — {a}، B — {b}.'},
}


def _round(value: float) -> int:
    """Round half up, as a reader expects: 62.5 -> 63 (Python's round gives 62)."""
    return math.floor(value + 0.5)


def points(level: int | None) -> int | None:
    return None if level is None else (level - 1) * 25


def _percent(found: int, total: int) -> int:
    return _round(100 * found / total)


def _reference_groups(takhrij: dict | None) -> list[tuple[str, dict]]:
    """Hadith takhrij and verse references are separate rows; a group without units gives no row."""
    if not takhrij:
        return []
    groups = [('takhrij', takhrij), ('verse_refs', takhrij.get('verses'))]
    return [(key, group) for key, group in groups if group and group.get('total')]


def seam_cap(seams: dict | None) -> dict:
    """Highest judge level of seamless assembly that the breaks found by the code allow.

    A sentence broken at a join is a seam defect: the judge cannot grade it as flawless.
    1 break -> level 4; 2-3 -> level 3; more -> level 2.
    """
    caps = {}
    for side in ('a', 'b'):
        broken = ((seams or {}).get(side) or {}).get('broken') or 0
        if broken:
            caps[side] = 4 if broken == 1 else 3 if broken <= 3 else 2
    return caps


def sides_without_notes(structural: dict | None, takhrij: dict | None) -> set:
    """Sides that give no scholarly apparatus although the source gives references.

    An apparatus is anchored notes, a glossary or a person index; the code counts them
    (apparatus_inventory), no model takes part. References inside the author's sentences
    alone are not an apparatus.
    """
    if not structural or not _reference_groups(takhrij):
        return set()
    parts = ('notes', 'glossary', 'persons')
    return {s for s in ('a', 'b')
            if not any(((structural.get(s) or {}).get('inventory') or {}).get(p) for p in parts)}


def jury_table(rubric: dict | None, coverage: dict | None, takhrij: dict | None = None,
               without_notes: set | frozenset = frozenset(), editing: dict | None = None,
               seams: dict | None = None) -> dict | None:
    if not rubric:
        return None
    indexed = {row['criterion']: row for row in rubric['criteria']}
    rows = []
    for name in RUBRIC:
        if name in indexed:
            levels = {s: indexed[name][s]['score'] for s in ('a', 'b')}
            row = {'key': name, 'kind': 'criterion'}
            if name == 'seamlessness' and seam_cap(seams):
                caps = seam_cap(seams)
                levels |= {s: min(levels[s], cap) for s, cap in caps.items() if levels[s] is not None}
                row['seam_breaks'] = {s: seams[s]['broken'] for s in caps}
            if name == 'apparatus' and without_notes:
                # No notes: the lowest level, whatever the judge wrote.
                levels |= {s: 1 for s in without_notes}
                row['no_notes'] = sorted(without_notes)
            rows.append(row | {'a': points(levels['a']), 'b': points(levels['b']), 'level': levels})
    critical = rubric.get('critical_errors')
    if critical is not None:
        # A count of errors, not points: it stays out of the total (_points_rows).
        rows.append({'key': 'critical', 'kind': 'critical', 'a': len(critical['a']), 'b': len(critical['b']),
                     'errors': critical})
    for key in COVERAGE_KEYS:
        counts = (coverage or {}).get(key)
        if counts and counts['total']:
            rows.append({'key': key, 'kind': 'coverage', 'a': _percent(counts['a'], counts['total']),
                         'b': _percent(counts['b'], counts['total']),
                         'found': {'a': counts['a'], 'b': counts['b']}, 'total': counts['total']})
    for key, group in _reference_groups(takhrij):
        # A wrong reference cancels a delivered one: a reader cannot tell which of them to trust.
        rows.append({'key': key, 'kind': 'takhrij',
                     **{s: _percent(max(0, group[s]['delivered'] - group[s]['wrong']), group['total'])
                        for s in ('a', 'b')},
                     'delivered': {s: group[s]['delivered'] for s in ('a', 'b')},
                     'wrong': {s: group[s]['wrong'] for s in ('a', 'b')}, 'total': group['total']})
    if seams and any(seams[s]['joins'] for s in ('a', 'b')):
        # Seams (seam_check): joins of two prose paragraphs without a broken sentence.
        rows.append({'key': 'seams', 'kind': 'seams',
                     **{s: _percent(seams[s]['joins'] - seams[s]['broken'], seams[s]['joins'])
                        if seams[s]['joins'] else 100 for s in ('a', 'b')},
                     'joins': {s: seams[s]['joins'] for s in ('a', 'b')},
                     'broken': {s: seams[s]['broken'] for s in ('a', 'b')}})
    if editing and any(editing[s].get('done_edits') for s in ('a', 'b')):
        # Only when a side has measured editing work; without receipts the row tells nothing new.
        # Editing: the part of the whole editing work that is done before the reader gets the text.
        # Done = applied audit and editor edits with receipts; remaining = edits that an editor still
        # has to make (errors with quotations, missing quotations and references).
        done = {s: editing[s].get('done_edits') or 0 for s in ('a', 'b')}
        remaining = {s: editing[s]['edits'] for s in ('a', 'b')}
        rows.append({'key': 'editing', 'kind': 'editing',
                     **{s: _percent(done[s], done[s] + remaining[s]) if done[s] + remaining[s] else 100
                        for s in ('a', 'b')},
                     'done': done, 'remaining': remaining})
    totals, winner = _total(rows)
    return {'version': VERSION, 'rows': rows, 'totals': totals, 'winner': winner}


def _points_rows(rows: list) -> list:
    """Rows with points 0-100 for both sides; a count of critical errors is not points."""
    return [r for r in rows if r['kind'] != 'critical' and r['a'] is not None and r['b'] is not None]


def _total(rows: list) -> tuple[dict, str | None]:
    # The total compares like with like: only rows with points for both sides.
    both = _points_rows(rows)
    totals = {s: _round(sum(r[s] for r in both) / len(both)) if both else None for s in ('a', 'b')}
    winner = None
    if both:
        winner = 'tie' if totals['a'] == totals['b'] else 'a' if totals['a'] > totals['b'] else 'b'
    return totals, winner


def effort_reduction(rubric: dict | None, coverage: dict | None, processing: dict | None,
                     takhrij: dict | None = None) -> dict | None:
    """Editing time that remains to reach the same standard, with the assumptions stated."""
    if not rubric:
        return None
    sides = {}
    for side in ('a', 'b'):
        defects = (rubric.get('unique_defects') or {}).get(side, 0)
        missing = sum(c['total'] - c[side] for c in (coverage or {}).values() if c and c['total'])
        measured = ((processing or {}).get('sides') or {}).get(side) or {}
        review_seconds = measured.get('simulated_seconds') or 0
        review = _round(review_seconds / 60)
        # Each reference that is missing or wrong is one edit: the editor adds or corrects it.
        references = sum(g['total'] - g[side]['delivered'] + g[side]['wrong'] for _, g in _reference_groups(takhrij))
        edits = defects + missing + references
        # Applied audit and editor edits with receipts: work that an editor does not have to do.
        done = (measured.get('audit_operations') or 0) + (measured.get('editor_operations') or 0)
        sides[side] = {'edits': edits, 'defects': defects, 'missing_quotations': missing, 'references': references,
                       'review_minutes': review, 'minutes': _round(edits * MINUTES_PER_EDIT + review_seconds / 60),
                       'done_edits': done, 'done_minutes': done * MINUTES_PER_EDIT}
    a, b = sides['a']['minutes'], sides['b']['minutes']
    return sides | {'reduction_percent': _round(100 * (1 - b / a)) if a else None,
                    'minutes_per_edit': MINUTES_PER_EDIT, 'version': EFFORT_VERSION}


def jury_summary(table: dict | None) -> dict | None:
    if not table or table['winner'] is None:
        return None
    totals = table['totals']
    better = {'a': [], 'b': []}
    equal = []
    for row in _points_rows(table['rows']):
        gap = row['b'] - row['a']
        (better['b'] if gap > 0 else better['a'] if gap < 0 else equal).append((row['key'], abs(gap)))
    text = {}
    for lang, phrase in PHRASES.items():
        label, comma = LABELS[lang], phrase['comma']
        listed = lambda items: comma.join(f'{label[k]} (+{gap})' for k, gap in items)
        if table['winner'] == 'tie':
            lines = [phrase['tie'].format(a=totals['a'])]
        else:
            win, lose = table['winner'], 'a' if table['winner'] == 'b' else 'b'
            lines = [phrase['win'].format(win=win.upper(), high=totals[win], low=totals[lose])]
        for side in ('b', 'a'):
            if better[side]:
                lines.append(phrase['better'].format(side=side.upper()) + listed(better[side]) + '.')
        if equal:
            lines.append(phrase['equal'] + comma.join(label[k] for k, _ in equal) + '.')
        for row in table['rows']:
            if row['kind'] == 'critical':
                lines.append(phrase['critical'].format(a=row['a'], b=row['b']))
        text[lang] = lines
    return text


def second_opinion(rubric: dict | None, model: str, second: dict | None,
                   without_notes: set | frozenset = frozenset(), seams: dict | None = None) -> dict | None:
    """Two judges of different families on the same criteria; quotation counts are not repeated."""
    if not rubric or not second or not second.get('rubric'):
        return None
    tables = {'first': jury_table(rubric, None, without_notes=without_notes, seams=seams),
              'second': jury_table(second['rubric'], None, without_notes=without_notes, seams=seams)}
    # The second opinion compares the judges' criteria and critical errors; code rows stay out of it.
    for table in tables.values():
        table['rows'] = [r for r in table['rows'] if r['kind'] in ('criterion', 'critical')]
        table['totals'], table['winner'] = _total(table['rows'])
    second_rows = {r['key']: r for r in tables['second']['rows']}
    rows = [{'key': r['key'], 'first': {'a': r['a'], 'b': r['b']},
             'second': {'a': second_rows[r['key']]['a'], 'b': second_rows[r['key']]['b']}}
            for r in tables['first']['rows'] if r['key'] in second_rows]
    summary = lambda table: {'totals': table['totals'], 'winner': table['winner']}
    return {'first': {'model': model} | summary(tables['first']),
            'second': {'model': second['model']} | summary(tables['second']) | {'run_id': second.get('run_id')},
            'rows': rows, 'agree': tables['first']['winner'] == tables['second']['winner']}
