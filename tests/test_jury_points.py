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
    assert result['a'] == {'edits': 9, 'defects': 6, 'missing_quotations': 3, 'references': 0,
                           'review_minutes': 0, 'minutes': 27}
    assert result['b'] == {'edits': 1, 'defects': 1, 'missing_quotations': 0, 'references': 0,
                           'review_minutes': 2, 'minutes': 5}
    assert result['reduction_percent'] == 81  # 1 - 5/27
    assert result['minutes_per_edit'] == 3 and result['version'] == 'effort-v2'


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


def test_equal_totals_read_naturally_in_russian():
    summary = jury_summary(jury_table(rubric({'accuracy': (4, 4)}), None))
    assert summary['ru'][0] == 'Переводы равны: итог 75 из 100 у каждого.'
    assert summary['en'][0] == 'The translations are equal: 75 points each.'


def test_second_opinion_compares_criteria_of_two_judges_and_names_agreement():
    from independent_judge.domain.jury_points import second_opinion
    first = rubric({'accuracy': (2, 4), 'completeness': (3, 5)})
    second = {'model': 'spacexai/grok-4.1-fast-reasoning', 'run_id': 'r2',
              'rubric': rubric({'accuracy': (4, 5), 'completeness': (3, 4)})}
    result = second_opinion(first, 'google/gemini-3.8-flash', second)
    assert result['first'] == {'model': 'google/gemini-3.8-flash', 'totals': {'a': 38, 'b': 88}, 'winner': 'b'}
    assert result['second'] == {'model': 'spacexai/grok-4.1-fast-reasoning', 'totals': {'a': 63, 'b': 88},
                                'winner': 'b', 'run_id': 'r2'}
    assert result['rows'][0] == {'key': 'accuracy', 'first': {'a': 25, 'b': 75}, 'second': {'a': 75, 'b': 100}}
    assert result['agree'] is True
    other = second | {'rubric': rubric({'accuracy': (5, 2), 'completeness': (5, 2)})}
    assert second_opinion(first, 'g', other)['agree'] is False
    assert second_opinion(first, 'g', None) is None and second_opinion(None, 'g', second) is None


def test_half_points_round_up():
    assert jury_table(rubric({'accuracy': (4, 4), 'completeness': (3, 3)}), None)['totals'] == {'a': 63, 'b': 63}


def test_summary_has_arabic_lines():
    summary = jury_summary(jury_table(rubric(PAIRS), COVERAGE))
    assert summary['ar'] == [
        'الترجمة B أفضل: 85 مقابل 55 نقطة.',
        'B أفضل في: الدقة (+25)، الاكتمال (+75)، آيات القرآن (+75).',
        'A أفضل في: سهولة القراءة (+25).',
        'متساويتان في: المصطلحات.']
    tie = jury_summary(jury_table(rubric({'accuracy': (4, 4)}), None))
    assert tie['ar'][0] == 'الترجمتان متساويتان: 75 نقطة لكل منهما.'


TAKHRIJ = {'version': 'takhrij-v1', 'total': 10, 'a': {'delivered': 3, 'wrong': 1, 'items': []},
           'b': {'delivered': 9, 'wrong': 0, 'items': []}}


def test_takhrij_row_counts_delivered_references_less_wrong_ones():
    table = jury_table(rubric({'accuracy': (4, 4)}), None, TAKHRIJ)
    row = next(r for r in table['rows'] if r['key'] == 'takhrij')
    assert row == {'key': 'takhrij', 'kind': 'takhrij', 'a': 20, 'b': 90, 'delivered': {'a': 3, 'b': 9},
                   'wrong': {'a': 1, 'b': 0}, 'total': 10}
    assert table['totals'] == {'a': 48, 'b': 83}  # (75 + 20) / 2 and (75 + 90) / 2


def test_effort_adds_one_edit_for_each_missing_or_wrong_reference():
    result = effort_reduction(rubric(PAIRS, defects=(6, 1)), COVERAGE, None, TAKHRIJ)
    assert result['a']['references'] == 8 and result['b']['references'] == 1  # 7 missing + 1 wrong; 1 missing
    assert result['a']['edits'] == 6 + 3 + 8 and result['version'] == 'effort-v2'


def test_takhrij_label_is_in_every_summary_language():
    summary = jury_summary(jury_table(rubric({'accuracy': (4, 4)}), None, TAKHRIJ))
    assert summary['en'][1] == 'B is better in: takhrij references (+70).'
    assert summary['ru'][1] == 'B лучше в: тахридж (+70).'
    assert summary['ar'][1] == 'B أفضل في: التخريج (+70).'
