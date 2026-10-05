"""The portable HTML report follows the protocol of the saved run."""
from independent_judge.application.comparison_view import _view
from independent_judge.infrastructure.comparison_report import comparison_html
from test_comparison_summary import record


def _side(score, status='assessed', **extra):
    return {'score': score, 'status': status, 'pass_scores': [score, score],
            'coverage': ['whole_selected_range', 'whole_selected_range'],
            'explanations': [{'explanation_en': 'Compared.', 'explanation_ru': 'Сопоставлено с оригиналом.'}],
            'evidence': [{'id': 'e1', 'kind': 'defect', 'verified': True, 'pass': 1,
                          'source_quote': 'First claim.', 'translation_quote': 'One claim.',
                          'explanation_en': 'Reversal.', 'explanation_ru': 'Смысл искажён.'}]} | extra


def paired_record(status='completed'):
    data = record()
    run = data['run']
    run['manifest']['protocol_version'] = 'paired-rubric-v1'
    run.update(status=status, findings={}, passes=[])
    run['paired'] = {'version': 'paired-rubric-v1', 'advantage': 'b', 'unique_defects': {'a': 1, 'b': 0},
                     'criteria': [{'criterion': 'accuracy', 'a': _side(2), 'b': _side(4)},
                                  {'criterion': 'apparatus', 'a': _side(None, 'unstable', evidence_conflict=True),
                                   'b': _side(None, 'not_applicable', evidence=[])}]}
    return data


def test_paired_run_does_not_produce_legacy_zero_counts():
    view = _view(paired_record())
    assert view['summary']['sides']['a']['candidates'] is None
    assert view['effort']['reduction_percent'] is None


def test_html_export_shows_paired_grades_evidence_and_processing_time():
    html = comparison_html(_view(paired_record()))
    assert 'На этом материале преимущество у B' in html
    assert '2 / 5' in html and '4 / 5' in html
    assert 'Неустойчиво' in html and 'противоположным выводам' in html
    assert 'Не применимо' in html
    assert 'Смысл искажён.' in html and 'One claim.' in html
    assert 'Уникальные привязанные кандидаты на ошибки: A — 1; B — 0' in html
    assert 'Время не установлено' in html
    assert 'находок — 0' not in html
    assert 'Кандидаты на проверку, включая спорные' not in html


def test_incomplete_paired_run_is_not_assessed_rather_than_zero():
    html = comparison_html(_view(paired_record(status='failed')))
    assert 'По парной методике не оценено' in html
    assert '/ 5' not in html
    assert 'находок — 0' not in html


def test_legacy_run_keeps_its_own_report():
    html = comparison_html(_view(record()))
    assert 'Кандидаты на проверку, включая спорные' in html
    assert 'По парной методике' not in html
