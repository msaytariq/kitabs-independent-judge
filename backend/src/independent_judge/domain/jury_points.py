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
           'readability': 'readability', 'seamlessness': 'assembly integrity',
           'apparatus': 'scholarly apparatus', 'quran': 'Quran verses', 'hadith': 'hadith',
           'takhrij': 'takhrij references'},
    'ru': {'accuracy': 'точность', 'completeness': 'полнота', 'terminology': 'терминология',
           'readability': 'читаемость', 'seamlessness': 'целостность сборки',
           'apparatus': 'научный аппарат', 'quran': 'аяты Корана', 'hadith': 'хадисы',
           'takhrij': 'тахридж'},
    'ar': {'accuracy': 'الدقة', 'completeness': 'الاكتمال', 'terminology': 'المصطلحات',
           'readability': 'سهولة القراءة', 'seamlessness': 'سلامة التجميع',
           'apparatus': 'الجهاز العلمي', 'quran': 'آيات القرآن', 'hadith': 'الأحاديث',
           'takhrij': 'التخريج'},
}
PHRASES = {
    'en': {'tie': 'The translations are equal: {a} points each.',
           'win': 'Translation {win} is better: {high} against {low} points.',
           'better': '{side} is better in: ', 'equal': 'Equal in: ', 'comma': ', '},
    'ru': {'tie': 'Переводы равны: итог {a} из 100 у каждого.',
           'win': 'Перевод {win} лучше: {high} против {low} баллов.',
           'better': '{side} лучше в: ', 'equal': 'Одинаково: ', 'comma': ', '},
    'ar': {'tie': 'الترجمتان متساويتان: {a} نقطة لكل منهما.',
           'win': 'الترجمة {win} أفضل: {high} مقابل {low} نقطة.',
           'better': '{side} أفضل في: ', 'equal': 'متساويتان في: ', 'comma': '، '},
}


def _round(value: float) -> int:
    """Round half up, as a reader expects: 62.5 -> 63 (Python's round gives 62)."""
    return math.floor(value + 0.5)


def points(level: int | None) -> int | None:
    return None if level is None else (level - 1) * 25


def _percent(found: int, total: int) -> int:
    return _round(100 * found / total)


def sides_without_notes(structural: dict | None, takhrij: dict | None) -> set:
    """Sides that give no anchored note although the source gives references to deliver.

    The code counts the notes (apparatus_inventory); no model takes part. References
    inside the author's sentences are not an apparatus.
    """
    if not structural or not takhrij or not takhrij.get('total'):
        return set()
    return {s for s in ('a', 'b') if not ((structural.get(s) or {}).get('inventory') or {}).get('notes')}


def jury_table(rubric: dict | None, coverage: dict | None, takhrij: dict | None = None,
               without_notes: set | frozenset = frozenset()) -> dict | None:
    if not rubric:
        return None
    indexed = {row['criterion']: row for row in rubric['criteria']}
    rows = []
    for name in RUBRIC:
        if name in indexed:
            levels = {s: indexed[name][s]['score'] for s in ('a', 'b')}
            row = {'key': name, 'kind': 'criterion'}
            if name == 'apparatus' and without_notes:
                # No notes: the lowest level, whatever the judge wrote.
                levels |= {s: 1 for s in without_notes}
                row['no_notes'] = sorted(without_notes)
            rows.append(row | {'a': points(levels['a']), 'b': points(levels['b']), 'level': levels})
    for key in COVERAGE_KEYS:
        counts = (coverage or {}).get(key)
        if counts and counts['total']:
            rows.append({'key': key, 'kind': 'coverage', 'a': _percent(counts['a'], counts['total']),
                         'b': _percent(counts['b'], counts['total']),
                         'found': {'a': counts['a'], 'b': counts['b']}, 'total': counts['total']})
    if takhrij and takhrij.get('total'):
        # A wrong reference cancels a delivered one: a reader cannot tell which of them to trust.
        rows.append({'key': 'takhrij', 'kind': 'takhrij',
                     **{s: _percent(max(0, takhrij[s]['delivered'] - takhrij[s]['wrong']), takhrij['total'])
                        for s in ('a', 'b')},
                     'delivered': {s: takhrij[s]['delivered'] for s in ('a', 'b')},
                     'wrong': {s: takhrij[s]['wrong'] for s in ('a', 'b')}, 'total': takhrij['total']})
    # The total compares like with like: only rows with a value for both sides.
    both = [r for r in rows if r['a'] is not None and r['b'] is not None]
    totals = {s: _round(sum(r[s] for r in both) / len(both)) if both else None for s in ('a', 'b')}
    winner = None
    if both:
        winner = 'tie' if totals['a'] == totals['b'] else 'a' if totals['a'] > totals['b'] else 'b'
    return {'version': VERSION, 'rows': rows, 'totals': totals, 'winner': winner}


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
        references = (takhrij['total'] - takhrij[side]['delivered'] + takhrij[side]['wrong']) if takhrij else 0
        edits = defects + missing + references
        sides[side] = {'edits': edits, 'defects': defects, 'missing_quotations': missing, 'references': references,
                       'review_minutes': review, 'minutes': _round(edits * MINUTES_PER_EDIT + review_seconds / 60)}
    a, b = sides['a']['minutes'], sides['b']['minutes']
    return sides | {'reduction_percent': _round(100 * (1 - b / a)) if a else None,
                    'minutes_per_edit': MINUTES_PER_EDIT, 'version': EFFORT_VERSION}


def jury_summary(table: dict | None) -> dict | None:
    if not table or table['winner'] is None:
        return None
    totals = table['totals']
    better = {'a': [], 'b': []}
    equal = []
    for row in table['rows']:
        if row['a'] is None or row['b'] is None:
            continue
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
        text[lang] = lines
    return text


def second_opinion(rubric: dict | None, model: str, second: dict | None,
                   without_notes: set | frozenset = frozenset()) -> dict | None:
    """Two judges of different families on the same criteria; quotation counts are not repeated."""
    if not rubric or not second or not second.get('rubric'):
        return None
    tables = {'first': jury_table(rubric, None, without_notes=without_notes),
              'second': jury_table(second['rubric'], None, without_notes=without_notes)}
    second_rows = {r['key']: r for r in tables['second']['rows']}
    rows = [{'key': r['key'], 'first': {'a': r['a'], 'b': r['b']},
             'second': {'a': second_rows[r['key']]['a'], 'b': second_rows[r['key']]['b']}}
            for r in tables['first']['rows'] if r['key'] in second_rows]
    summary = lambda table: {'totals': table['totals'], 'winner': table['winner']}
    return {'first': {'model': model} | summary(tables['first']),
            'second': {'model': second['model']} | summary(tables['second']) | {'run_id': second.get('run_id')},
            'rows': rows, 'agree': tables['first']['winner'] == tables['second']['winner']}
