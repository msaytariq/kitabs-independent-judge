"""The portable HTML report follows the protocol of the saved run."""
from independent_judge.application.comparison_view import _view
from independent_judge.infrastructure.comparison_report import comparison_html
from test_comparison_summary import record


def _side(score, status='assessed', **extra):
    return {'score': score, 'status': status, 'explanation_en': 'Compared.',
            'explanation_ru': 'Сопоставлено с оригиналом.',
            'evidence': [{'id': 'e1', 'kind': 'defect', 'verified': True,
                          'source_quote': 'First claim.', 'translation_quote': 'One claim.',
                          'explanation_en': 'Reversal.', 'explanation_ru': 'Смысл искажён.'}]} | extra


def rubric_record(status='completed'):
    data = record()
    run = data['run']
    run['manifest']['protocol_version'] = 'rubric-v1'
    run.update(status=status, findings={}, passes=[])
    run['rubric'] = {'version': 'rubric-v1', 'winner': 'b', 'totals': {'a': 2.5, 'b': 4.0},
                     'unique_defects': {'a': 1, 'b': 0},
                     'criteria': [{'criterion': 'accuracy', 'a': _side(2), 'b': _side(4)},
                                  {'criterion': 'terminology', 'a': _side(3), 'b': _side(4)},
                                  {'criterion': 'apparatus', 'a': _side(None, 'not_applicable', evidence=[]),
                                   'b': _side(None, 'not_applicable', evidence=[])}]}
    hashes = data['scope']['hashes']
    data['processing'] = {'b': {'job_id': 'job', 'state': 'completed', 'source_sha256': hashes['source'],
        'text_sha256': hashes['b'], 'timing_complete': True, 'intervals': [{'start': 0, 'end': 116.042259}],
        'operations_complete': True, 'operations': []}}
    return data


def test_rubric_run_does_not_produce_legacy_zero_counts():
    view = _view(rubric_record())
    assert view['summary']['sides']['a']['candidates'] is None
    assert view['effort']['reduction_percent'] is None


def test_html_export_shows_definite_grades_total_winner_and_time():
    html = comparison_html(_view(rubric_record()))
    assert 'Лучше перевод B' in html
    assert '<b>25</b>' in html and '<b>75</b>' in html and 'уровень 2 из 5' in html
    # A: 25 and 50 -> 38; B: 75 and 75 -> 75. Apparatus has no grade for either side.
    assert 'Итог, 0–100' in html and '<b>38</b>' in html and '<b>75</b>' in html
    assert '100 — замечаний нет' in html
    assert 'Смысл искажён.' in html and 'One claim.' in html
    assert 'Ошибки с цитатами: A — 1; B — 0' in html
    assert 'Перевод B лучше: 75 против 38 баллов.' in html
    assert '<td>116</td>' in html and '116.04' not in html
    assert html.count('Время не установлено') == 1
    for word in ('Неустойчиво', 'Не оценено', 'не оценено', 'Проходы', 'находок — 0', 'Кандидаты на проверку'):
        assert word not in html


def test_html_export_shows_the_editing_time_that_remains():
    html = comparison_html(_view(rubric_record()))
    assert 'Редактура до публикации' in html
    # A: 1 defect x 3 min = 3 min; B: 0 defects and no applied edits = 0 min.
    assert '<tr><th>Осталось правок</th><td>1</td><td>0</td></tr>' in html
    assert '<tr><th>Время редактора, минуты</th><td>3</td><td>0</td></tr>' in html
    assert 'Экономия времени с B: 100%' in html
    assert '3 минуты на одну правку' in html


def test_incomplete_rubric_run_reports_failure_without_zero():
    html = comparison_html(_view(rubric_record(status='failed')))
    assert 'Оценка не завершена' in html
    assert '/ 5' not in html and 'Итог, 0–100' not in html


def test_legacy_run_keeps_its_own_report():
    html = comparison_html(_view(record()))
    assert 'Кандидаты на проверку, включая спорные' in html
    assert 'Лучше перевод' not in html


def test_html_export_shows_source_reference_counts_and_wrong_labels():
    data = rubric_record()
    data['hadith'] = {'status': 'checked',
        'quran': {'found': 5, 'total': 5, 'label_differs': 1, 'items': [
            {'quote': 'استعينوا بالصبر', 'status': 'found', 'ayah': '2:153', 'surah_name': 'البقرة',
             'label': 'محمد : 31', 'label_status': 'label_differs'}]},
        'hadith': {'found': 2, 'total': 3, 'by_collection': {'Sahih Muslim': 2}, 'items': [
            {'quote': 'عجبا لأمر المؤمن', 'status': 'fragment', 'candidate_count': 1, 'candidates': [
                {'id': 'muslim:1', 'collection': 'Sahih Muslim', 'number': 1, 'url': 'https://example.org/1'}]}]}}
    html = comparison_html(_view(data))
    assert 'Аяты Корана: найдено 5 из 5' in html
    assert 'Ошибка ссылки в оригинале: «محمد : 31», в Коране — 2:153' in html
    assert 'Хадисы: найдено 2 из 3' in html and 'Sahih Muslim — 2' in html


def test_table_rows_count_verses_and_hadith_in_each_translation():
    data = rubric_record()
    data['hadith'] = {'status': 'checked', 'quran': {'found': 2, 'total': 2, 'label_differs': 0,
        'items': [{'start': 1, 'quote': 'x', 'status': 'found', 'ayah': '1:1', 'surah_name': 'الفاتحة', 'label_status': 'no_label'},
                  {'start': 9, 'quote': 'y', 'status': 'found', 'ayah': '1:2', 'surah_name': 'الفاتحة', 'label_status': 'no_label'}]},
        'hadith': {'found': 1, 'total': 1, 'by_collection': {}, 'items': [{'start': 20, 'quote': 'z', 'status': 'fragment', 'candidates': []}]}}
    side = lambda present: {'present': present, 'quote': None, 'claimed': present}
    data['coverage'] = {'items': [{'start': 1, 'a': side(False), 'b': side(True)}, {'start': 9, 'a': side(False), 'b': side(True)},
                                  {'start': 20, 'a': side(True), 'b': side(True)}]}
    view = _view(data)
    assert view['reference_coverage'] == {'quran': {'total': 2, 'a': 0, 'b': 2}, 'hadith': {'total': 1, 'a': 1, 'b': 1}}
    html = comparison_html(view)
    assert '<tr><th>Аяты Корана в переводе</th><td><b>0</b><br>0 из 2</td><td><b>100</b><br>2 из 2</td></tr>' in html
    assert '<tr><th>Хадисы в переводе</th><td><b>100</b><br>1 из 1</td><td><b>100</b><br>1 из 1</td></tr>' in html
    assert view['jury']['totals'] == {'a': 44, 'b': 88}  # A: 25, 50, 0, 100; B: 75, 75, 100, 100


def test_html_export_names_a_when_a_needs_less_editing():
    from independent_judge.infrastructure.rubric_report import _effort_html
    side = lambda minutes: {'edits': 1, 'defects': 1, 'missing_quotations': 0, 'review_minutes': 0, 'minutes': minutes}
    html = _effort_html({'a': side(3), 'b': side(8), 'reduction_percent': -167, 'minutes_per_edit': 3})
    assert 'A требует меньше редактуры: 3 против 8 минут' in html and '-167' not in html


def test_html_export_shows_what_the_judge_caught():
    html = comparison_html(_view(rubric_record()))
    assert 'Что поймал судья' in html
    assert 'Перевод A · точность' in html and '<blockquote dir="auto">One claim.</blockquote>' in html
    assert 'Перевод B · точность' in html  # The fixture gives B the same quoted error.


def test_html_export_shows_the_second_judge():
    data = rubric_record()
    data['run']['manifest']['actual_models'] = ['google/gemini-3.8-flash']
    data['second_judge'] = {'model': 'spacexai/grok-4.1-fast-reasoning', 'run_id': 'second', 'rubric': data['run']['rubric']}
    html = comparison_html(_view(data))
    assert 'Второй судья' in html and 'spacexai/grok-4.1-fast-reasoning' in html
    assert 'Победитель совпал: B' in html


def test_report_shows_the_takhrij_row():
    from independent_judge.application.comparison_view import _view
    from independent_judge.infrastructure.rubric_report import rubric_html
    takhrij = {'version': 'takhrij-v1', 'total': 4, 'a': {'delivered': 1, 'wrong': 2, 'items': []},
               'b': {'delivered': 4, 'wrong': 0, 'items': []}}
    html = rubric_html(_view(rubric_record() | {'hadith': {'status': 'checked', 'takhrij': takhrij}}))
    assert 'Тахридж' in html and 'верных 1 из 4, неверных 2' in html


def test_report_shows_the_editing_row():
    from independent_judge.infrastructure.rubric_report import rubric_html
    view = _view(rubric_record())
    view['jury']['rows'].append({'key': 'editing', 'kind': 'editing', 'a': 0, 'b': 92,
                                 'done': {'a': 0, 'b': 69}, 'remaining': {'a': 41, 'b': 6}})
    html = rubric_html(view)
    assert 'Редактура: доля выполненной правки' in html and 'сделано 69, осталось 6' in html


def test_html_export_shows_the_critical_errors_and_who_corrects_them():
    data = rubric_record()
    error = {'id': 'c1', 'side': 'a', 'category': 'meaning_reversed', 'verified': True,
             'source_quote': 'First claim.', 'translation_quote': 'One claim.',
             'explanation_en': 'Reversal.', 'explanation_ru': 'Смысл перевёрнут.'}
    data['run']['rubric']['critical_errors'] = {'a': [error], 'b': []}
    html = comparison_html(_view(data))
    assert '<tr><th>Критические ошибки, число</th><td><b>1</b>' in html and '<td><b>0</b></td>' in html
    assert 'Смысл перевёрнут.' in html
    assert 'В итог не входит' in html
    assert 'аудит и редактор предлагают правку, человек принимает или отклоняет её' in html
    # The total stays the mean of the points rows.
    assert '<b>38</b>' in html
