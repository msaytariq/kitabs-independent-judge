"""Each Quran verse and hadith of the original is counted in A and B only with a real quotation."""
import json
from decimal import Decimal
import pytest
from independent_judge.domain.evaluation import EvaluationError, JudgeConfig, LlmResult
from independent_judge.domain.reference_coverage import coverage_prompt, parse_coverage, coverage_counts
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository

SOURCE = ('قال تعالى: ﴿وجعل بينكم مودة ورحمة﴾ وقال رسول الله ﷺ: «خيركم خيركم لأهله» '
          'وقال ﷺ: «كلكم راع وكلكم مسؤول عن رعيته».')
A = 'The Prophet said: "The best of you are the best to their families."'
B = ('Allah says: "He placed between you affection and mercy." The Prophet said: "The best of you are '
     'the best to their families." He also said: "Each of you is a shepherd and responsible for his flock."')


def answer(**changes):
    rows = [{'id': 0, 'a': {'present': False, 'quote': None}, 'b': {'present': True, 'quote': 'He placed between you affection and mercy.'}},
            {'id': 1, 'a': {'present': True, 'quote': 'The best of you are the best to their families.'},
             'b': {'present': True, 'quote': 'The best of you are the best to their families.'}},
            {'id': 2, 'a': {'present': True, 'quote': 'Each of you is a shepherd'},
             'b': {'present': True, 'quote': 'Each of you is a shepherd and responsible for his flock.'}}]
    for key, value in changes.items():
        rows[int(key[1:])] = rows[int(key[1:])] | value
    return json.dumps({'items': rows})


def test_prompt_lists_every_detected_quotation_with_an_id():
    prompt = coverage_prompt({'source': SOURCE, 'a': A, 'b': B})
    data = json.loads(prompt.user)
    assert [i['id'] for i in data['quotations']] == [0, 1, 2]
    assert data['quotations'][0]['arabic'] == 'وجعل بينكم مودة ورحمة'
    assert data['translations'] == {'a': A, 'b': B}


def test_only_quotations_found_in_the_translation_count():
    result = parse_coverage(answer(), {'source': SOURCE, 'a': A, 'b': B})
    rows = {r['start']: r for r in result['items']}
    first, third = result['items'][0], result['items'][2]
    assert first['a']['present'] is False and first['b']['present'] is True
    assert third['a']['present'] is False  # A has no such sentence: an invented quote does not count
    assert result['totals'] == {'a': 1, 'b': 3, 'items': 3}
    assert len(rows) == 3


def test_counts_follow_the_reference_classification():
    coverage = parse_coverage(answer(), {'source': SOURCE, 'a': A, 'b': B})
    starts = [r['start'] for r in coverage['items']]
    references = {'quran': {'items': [{'start': starts[0]}]},
                  'hadith': {'items': [{'start': starts[1]}, {'start': starts[2]}]}}
    assert coverage_counts(references, coverage) == {
        'quran': {'total': 1, 'a': 0, 'b': 1}, 'hadith': {'total': 2, 'a': 1, 'b': 2}}
    assert coverage_counts(None, coverage) is None and coverage_counts(references, None) is None


def test_missing_or_extra_items_reject_the_answer():
    with pytest.raises(EvaluationError):
        parse_coverage(json.dumps({'items': []}), {'source': SOURCE, 'a': A, 'b': B})


class Judge:
    def __init__(self): self.calls = []
    def complete(self, prompt, config):
        self.calls.append(prompt)
        text = answer()
        return LlmResult(text, config.model, {}, Decimal('.001'), json.loads(text))


def test_coverage_runner_is_one_admitted_call_saved_as_its_own_run(tmp_path):
    from independent_judge.application.judge_runner import run_comparison
    from test_judge_contracts import sample
    from dataclasses import replace
    scope = sample()
    scope = replace(scope, texts={'source': SOURCE, 'a': A, 'b': B},
                    hashes={k: __import__('independent_judge.domain.scope', fromlist=['text_hash']).text_hash(v)
                            for k, v in {'source': SOURCE, 'a': A, 'b': B}.items()})
    judge = Judge()
    result = run_comparison(scope, JudgeConfig(), judge,
        BudgetLedger(tmp_path, total_usd=Decimal('1'), per_run_usd=Decimal('1')),
        RunRepository(tmp_path), run_id='coverage', code_sha='a' * 40, protocol='coverage-v1')
    assert result['status'] == 'completed' and len(judge.calls) == 1
    assert result['coverage']['totals'] == {'a': 1, 'b': 3, 'items': 3}
    assert result['manifest']['protocol_version'] == 'coverage-v1'
