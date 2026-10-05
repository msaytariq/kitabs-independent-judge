import importlib
import json
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import pytest
from test_judge_contracts import sample
from independent_judge.domain.evaluation import EvaluationError, JudgeConfig, LlmResult
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository

CRITERIA = ('accuracy', 'completeness', 'terminology', 'readability', 'seamlessness', 'apparatus')


def response(order=('a', 'b')):
    scope = sample()
    def side(key):
        return {'status': 'assessed', 'score': 2 if key == 'a' else 4,
                'coverage': 'whole_selected_range', 'explanation_en': 'Compared with source.',
                'explanation_ru': 'Сопоставлено с оригиналом.', 'evidence': [{
                    'source_quote': 'الصدق فضيلة', 'translation_quote': scope.texts[key],
                    'kind': 'defect' if key == 'a' else 'strength',
                    'explanation_en': 'Reversal.' if key == 'a' else 'Faithful.',
                    'explanation_ru': 'Искажение.' if key == 'a' else 'Точно.'}]}
    rows = [{'criterion': c, 'a': side(order[0]), 'b': side(order[1])} for c in CRITERIA]
    for s in ('a', 'b'):
        rows[-1][s].update(status='not_applicable', score=None, evidence=[])
    return {'criteria': rows}


def parse(data, order=('a', 'b'), scope=None):
    mod = importlib.import_module('independent_judge.domain.paired_assessment')
    return mod.parse_assessment(json.dumps(data), scope or sample(), order)


def reconcile(first, second, scope=None):
    mod = importlib.import_module('independent_judge.domain.paired_consensus')
    return mod.reconcile_assessments([first, second], scope or sample())


def test_order_is_reversed_back_before_scores_are_compared():
    result = reconcile(parse(response()), parse(response(('b', 'a')), ('b', 'a')))
    assert result['advantage'] == 'b'
    assert result['criteria'][0]['a']['score'] == 2
    assert result['criteria'][0]['b']['score'] == 4
    assert result['criteria'][-1]['a']['status'] == 'not_applicable'
    assert result['unique_defects'] == {'a': 1, 'b': 0}
    assert 'total' not in result


def test_disagreement_is_not_averaged_into_a_final_grade():
    second = response(('b', 'a'))
    second['criteria'][0]['b']['score'] = 4
    result = reconcile(parse(response()), parse(second, ('b', 'a')))
    a = result['criteria'][0]['a']
    assert a['score'] is None and a['status'] == 'unstable'
    assert a['pass_scores'] == [2, 4]
    assert result['advantage'] == 'none'


def test_opposite_conclusions_on_the_same_quotes_are_unstable_despite_equal_scores():
    second = response(('b', 'a'))
    evidence = second['criteria'][0]['b']['evidence'][0]
    evidence.update(kind='strength', explanation_en='Faithful.', explanation_ru='Смысл передан верно.')
    result = reconcile(parse(response()), parse(second, ('b', 'a')))
    a = result['criteria'][0]['a']
    assert a['score'] is None and a['status'] == 'unstable'
    assert a['evidence_conflict'] is True
    assert a['pass_scores'] == [2, 2]
    assert result['advantage'] == 'none'
    from independent_judge.application.paired_disputes import examine_disputes
    calls = []
    examine_disputes(sample(), result, lambda name, prompt: calls.append(name) or '{}')
    assert calls == ['paired-disputes']


def test_missing_or_ambiguous_quotes_cannot_support_a_score():
    data = response()
    data['criteria'][0]['a']['evidence'][0]['translation_quote'] = 'not in text'
    assert parse(data)['criteria'][0]['a']['status'] == 'unverified_evidence'
    scope = sample()
    repeated = replace(scope, texts=scope.texts | {'a': scope.texts['a'] * 2})
    assert parse(response(), scope=repeated)['criteria'][0]['a']['status'] == 'unverified_evidence'


def test_five_requires_full_coverage_and_positive_source_evidence():
    data = response()
    data['criteria'][0]['a'].update(score=5, coverage='partial')
    assert parse(data)['criteria'][0]['a']['status'] == 'unverified_evidence'
    data['criteria'][0]['a'].update(coverage='whole_selected_range', evidence=[])
    assert parse(data)['criteria'][0]['a']['status'] == 'unverified_evidence'


def test_symmetric_texts_with_asymmetric_scores_are_unstable():
    scope = sample()
    scope = replace(scope, texts=scope.texts | {'b': scope.texts['a']})
    data = response()
    for row in data['criteria']:
        for evidence in row['b']['evidence']:
            evidence['translation_quote'] = scope.texts['a']
    parsed = parse(data, scope=scope)
    result = reconcile(parsed, deepcopy(parsed), scope)
    assert result['criteria'][0]['a']['status'] == 'unstable'
    assert result['criteria'][0]['b']['score'] is None


def test_missing_criterion_and_invalid_scores_reject_entire_response():
    data = response()
    data['criteria'].pop()
    with pytest.raises(EvaluationError): parse(data)
    data = response()
    data['criteria'][0]['a']['score'] = True
    with pytest.raises(EvaluationError): parse(data)


class PairedJudge:
    def __init__(self): self.calls = []
    def complete(self, prompt, config):
        self.calls.append(prompt)
        texts = json.loads(prompt.user)
        order = ('a', 'b') if texts['translations']['a'] == sample().texts['a'] else ('b', 'a')
        raw = response(order)
        return LlmResult(json.dumps(raw), config.model, {}, Decimal('.001'), raw)


def run(tmp_path, total='3'):
    from independent_judge.application.judge_runner import run_comparison
    judge = PairedJudge()
    result = run_comparison(sample(), JudgeConfig(), judge,
        BudgetLedger(tmp_path, total_usd=Decimal(total), per_run_usd=Decimal(total)),
        RunRepository(tmp_path), run_id='paired', code_sha='a' * 40, protocol='paired-rubric-v1')
    return result, judge


def test_two_pass_runner_persists_receipts_and_keeps_vendor_names_out(tmp_path):
    result, judge = run(tmp_path)
    assert result['status'] == 'completed'
    assert result['paired']['advantage'] == 'b'
    assert len(judge.calls) == 2
    assert result['manifest']['protocol_version'] == 'paired-rubric-v1'
    assert result['cost']['reported_usd'] == '0.002000'
    assert RunRepository(tmp_path).get('paired') == result


def test_exhausted_budget_produces_no_grade_or_gateway_call(tmp_path):
    result, judge = run(tmp_path, '.01')
    assert result['status'] == 'budget_stopped'
    assert result['paired'] is None
    assert not judge.calls


def test_structural_signals_do_not_guess_external_chunk_boundaries():
    mod = importlib.import_module('independent_judge.domain.structural_checks')
    result = mod.structural_checks({'source': 'Original.', 'a': 'Repeat.\n\nRepeat.', 'b': 'Text [1].'})
    assert result['a']['chunk_boundary_coverage'] == 'unknown'
    assert result['a']['signals'][0]['confidence'] == 'heuristic'
    assert result['b']['signals'][0]['kind'] == 'unresolved_note_marker'


def test_targeted_dispute_pass_keeps_original_instability_visible(tmp_path):
    class Disagreement(PairedJudge):
        def complete(self, prompt, config):
            answer = super().complete(prompt, config)
            raw = json.loads(answer.text)
            if len(self.calls) == 2:
                raw['criteria'][0]['b']['score'] = 3
            if prompt.version == 'paired-disputes-v1':
                raw['criteria'] = raw['criteria'][:1]
            return replace(answer, text=json.dumps(raw), raw=raw)
    from independent_judge.application.judge_runner import run_comparison
    judge = Disagreement()
    result = run_comparison(sample(), JudgeConfig(), judge,
        BudgetLedger(tmp_path, total_usd=Decimal('3'), per_run_usd=Decimal('3')),
        RunRepository(tmp_path), run_id='dispute', code_sha='a' * 40, protocol='paired-rubric-v1')
    assert len(judge.calls) == 3
    assert result['paired']['criteria'][0]['a']['status'] == 'unstable'
    assert result['adjudication']['status'] == 'completed'
    assert len(result['adjudication']['result']['criteria']) == 1
