"""One judge pass gives one definite grade per criterion, a total and a winner."""
import importlib
import json
from decimal import Decimal
import pytest
from test_judge_contracts import sample
from independent_judge.domain.evaluation import EvaluationError, JudgeConfig, LlmResult
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository

CRITERIA = ('accuracy', 'completeness', 'terminology', 'readability', 'seamlessness', 'apparatus')


def response(a_score=2, b_score=4):
    scope = sample()
    def side(key, score):
        return {'status': 'assessed', 'score': score,
                'coverage': 'whole_selected_range', 'explanation_en': 'Compared with source.',
                'explanation_ru': 'Сопоставлено с оригиналом.', 'evidence': [{
                    'source_quote': 'الصدق فضيلة', 'translation_quote': scope.texts[key],
                    'kind': 'defect' if key == 'a' else 'strength',
                    'explanation_en': 'Reversal.' if key == 'a' else 'Faithful.',
                    'explanation_ru': 'Искажение.' if key == 'a' else 'Точно.'}]}
    rows = [{'criterion': c, 'a': side('a', a_score), 'b': side('b', b_score)} for c in CRITERIA]
    for s in ('a', 'b'):
        rows[-1][s].update(status='not_applicable', score=None, evidence=[])
    return {'criteria': rows}


def summarize(data, scope=None):
    parsing = importlib.import_module('independent_judge.domain.paired_assessment')
    result = importlib.import_module('independent_judge.domain.rubric_result')
    return result.summarize_assessment(parsing.parse_assessment(json.dumps(data), scope or sample()))


def test_one_pass_gives_definite_grades_total_and_winner():
    result = summarize(response())
    assert result['criteria'][0]['a']['score'] == 2 and result['criteria'][0]['b']['score'] == 4
    assert result['totals'] == {'a': 2.0, 'b': 4.0}
    assert result['winner'] == 'b'
    assert result['unique_defects'] == {'a': 1, 'b': 0}


def test_unlocated_quote_keeps_the_grade_but_is_not_shown_as_evidence():
    data = response()
    data['criteria'][0]['a']['evidence'][0]['translation_quote'] = 'not in text'
    row = summarize(data)['criteria'][0]['a']
    assert row['score'] == 2 and row['status'] == 'assessed'
    assert row['evidence'] == []


def test_five_is_kept_as_given():
    data = response(b_score=5)
    data['criteria'][0]['b']['coverage'] = 'partial'
    assert summarize(data)['criteria'][0]['b']['score'] == 5


def test_equal_totals_are_a_tie_and_unscored_rows_do_not_enter_the_total():
    data = response(a_score=3, b_score=3)
    data['criteria'][1]['b'].update(status='not_assessed', score=None)
    data['criteria'][1]['a']['score'] = 1
    result = summarize(data)
    assert result['totals'] == {'a': 3.0, 'b': 3.0}
    assert result['winner'] == 'tie'


def test_missing_criterion_and_invalid_scores_reject_entire_response():
    data = response()
    data['criteria'].pop()
    with pytest.raises(EvaluationError): summarize(data)
    data = response()
    data['criteria'][0]['a']['score'] = True
    with pytest.raises(EvaluationError): summarize(data)


class Judge:
    def __init__(self): self.calls = []
    def complete(self, prompt, config):
        self.calls.append(prompt)
        raw = response()
        return LlmResult(json.dumps(raw), config.model, {}, Decimal('.001'), raw)


def run(tmp_path, total='3'):
    from independent_judge.application.judge_runner import run_comparison
    judge = Judge()
    result = run_comparison(sample(), JudgeConfig(), judge,
        BudgetLedger(tmp_path, total_usd=Decimal(total), per_run_usd=Decimal(total)),
        RunRepository(tmp_path), run_id='rubric', code_sha='a' * 40, protocol='rubric-v1')
    return result, judge


def test_single_pass_runner_makes_one_call_and_keeps_vendor_names_out(tmp_path):
    result, judge = run(tmp_path)
    assert result['status'] == 'completed'
    assert result['rubric']['winner'] == 'b'
    assert len(judge.calls) == 2 and judge.calls[1].version == 'coverage-v1'
    assert result['coverage'] is None and result['coverage_error']['code'] == 'invalid_coverage_response'
    prompt = json.loads(judge.calls[0].user)
    assert prompt['translations'] == {'a': sample().texts['a'], 'b': sample().texts['b']}
    assert result['manifest']['protocol_version'] == 'rubric-v1'
    assert result['cost']['reported_usd'] == '0.002000'
    assert RunRepository(tmp_path).get('rubric') == result


def test_exhausted_budget_produces_no_grade_or_gateway_call(tmp_path):
    result, judge = run(tmp_path, '.01')
    assert result['status'] == 'budget_stopped'
    assert result['rubric'] is None
    assert not judge.calls


def test_structural_signals_do_not_guess_external_chunk_boundaries():
    mod = importlib.import_module('independent_judge.domain.structural_checks')
    result = mod.structural_checks({'source': 'Original.', 'a': 'Repeat.\n\nRepeat.', 'b': 'Text [1].'})
    assert result['a']['chunk_boundary_coverage'] == 'unknown'
    assert result['a']['signals'][0]['confidence'] == 'heuristic'
    assert result['b']['signals'][0]['kind'] == 'unresolved_note_marker'
