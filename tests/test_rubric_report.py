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
    assert '2 / 5' in html and '4 / 5' in html
    assert 'Итог' in html and '2,5 / 5' in html and '4,0 / 5' in html
    assert 'Смысл искажён.' in html and 'One claim.' in html
    assert 'Ошибки с цитатами: A — 1; B — 0' in html
    assert '<td>116</td>' in html and '116.04' not in html
    assert html.count('Время не установлено') == 1
    for word in ('Неустойчиво', 'Не оценено', 'не оценено', 'Проходы', 'находок — 0', 'Кандидаты на проверку'):
        assert word not in html


def test_incomplete_rubric_run_reports_failure_without_zero():
    html = comparison_html(_view(rubric_record(status='failed')))
    assert 'Оценка не завершена' in html
    assert '/ 5' not in html


def test_legacy_run_keeps_its_own_report():
    html = comparison_html(_view(record()))
    assert 'Кандидаты на проверку, включая спорные' in html
    assert 'Лучше перевод' not in html
