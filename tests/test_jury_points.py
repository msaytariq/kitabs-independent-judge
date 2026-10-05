"""The jury table shows points 0-100, the editing work that remains and a plain summary."""
from independent_judge.domain.jury_points import effort_reduction, jury_summary, jury_table, points


def side(score, defects=0):
    return {'score': score, 'status': 'assessed' if score else 'not_assessed', 'explanation_en': '',
            'explanation_ru': '', 'evidence': [{'id': f'd{i}', 'kind': 'defect', 'verified': True}
                                               for i in range(defects)]}


def rubric(pairs, defects=(0, 0)):
    return {'criteria': [{'criterion': name, 'a': side(a), 'b': side(b)} for name, (a, b) in pairs.items()],
            'unique_defects': {'a': defects[0], 'b': defects[1]}}


PAIRS = {'accuracy': (3, 4), 'completeness': (2, 5), 'terminology': (4, 4), 'readability': (5, 4)}
COVERAGE = {'quran': {'total': 4, 'a': 1, 'b': 4}, 'hadith': {'total': 0, 'a': 0, 'b': 0}}


def test_levels_become_points_from_0_to_100():
    assert [points(level) for level in (1, 2, 3, 4, 5)] == [0, 25, 50, 75, 100]
    assert points(None) is None


def test_table_adds_coverage_rows_and_averages_all_rows():
    table = jury_table(rubric(PAIRS), COVERAGE)
    rows = {r['key']: r for r in table['rows']}
    assert rows['accuracy'] == {'key': 'accuracy', 'kind': 'criterion', 'a': 50, 'b': 75,
                                'level': {'a': 3, 'b': 4}}
    assert rows['quran'] == {'key': 'quran', 'kind': 'coverage', 'a': 25, 'b': 100,
                             'found': {'a': 1, 'b': 4}, 'total': 4}
    assert 'hadith' not in rows  # The source has no hadith: no row, no free points.
    # A: 50, 25, 75, 100, 25 -> 55. B: 75, 100, 75, 75, 100 -> 85.
    assert table['totals'] == {'a': 55, 'b': 85}
    assert table['winner'] == 'b' and table['version'] == 'points-v1'


def test_a_criterion_graded_for_one_side_only_is_left_out_of_both_totals():
    table = jury_table(rubric({'accuracy': (5, 1), 'apparatus': (None, 5)}), None)
    assert table['totals'] == {'a': 100, 'b': 0}
    assert [r['b'] for r in table['rows'] if r['key'] == 'apparatus'] == [100]


def test_equal_totals_are_a_tie_and_no_rubric_gives_no_table():
    assert jury_table(rubric({'accuracy': (4, 4)}), None)['winner'] == 'tie'
    assert jury_table(None, COVERAGE) is None


def test_effort_counts_defects_and_missing_quotations_and_the_kitabs_review_time():
    effort = {'sides': {'a': {'total_seconds': None, 'simulated_seconds': None},
                        'b': {'total_seconds': 600, 'simulated_seconds': 120}}}
    result = effort_reduction(rubric(PAIRS, defects=(6, 1)), COVERAGE, effort)
    # A: 6 defects + 3 missing verses = 9 edits x 3 min = 27 min.
    # B: 1 defect = 3 min, plus 120 s of accepting Kitabs edits = 5 min.
    assert result['a'] == {'edits': 9, 'defects': 6, 'missing_quotations': 3, 'review_minutes': 0, 'minutes': 27}
    assert result['b'] == {'edits': 1, 'defects': 1, 'missing_quotations': 0, 'review_minutes': 2, 'minutes': 5}
    assert result['reduction_percent'] == 81  # 1 - 5/27
    assert result['minutes_per_edit'] == 3 and result['version'] == 'effort-v1'


def test_effort_reduction_is_not_shown_when_a_needs_no_work():
    result = effort_reduction(rubric(PAIRS, defects=(0, 2)), None, None)
    assert result['a']['minutes'] == 0 and result['reduction_percent'] is None
    assert effort_reduction(None, COVERAGE, None) is None


def test_summary_names_where_each_translation_is_better():
    summary = jury_summary(jury_table(rubric(PAIRS), COVERAGE))
    assert summary['en'] == [
        'Translation B is better: 85 against 55 points.',
        'B is better in: accuracy (+25), completeness (+75), Quran verses (+75).',
        'A is better in: readability (+25).',
        'Equal in: terminology.']
    assert summary['ru'][0] == 'Перевод B лучше: 85 против 55 баллов.'
    assert summary['ru'][1] == 'B лучше в: точность (+25), полнота (+75), аяты Корана (+75).'
    assert jury_summary(None) is None
