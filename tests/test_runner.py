"""End-to-end protocol with fixed provider responses and persistent cost admission."""
import json
from decimal import Decimal
from dataclasses import replace
import pytest
from test_judge_contracts import sample, finding
from independent_judge.domain.evaluation import JudgeConfig,LlmResult,EvaluationError
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository
from independent_judge.application.judge_runner import run_comparison


class FakeJudge:
    def __init__(self): self.calls=[]
    def complete(self,prompt,config):
        self.calls.append(prompt)
        data=json.loads(prompt.user)
        if prompt.version=='assessment-v1':
            result={'findings':[finding()] if data['translation']=='Truth is a vice.' else []}
        elif prompt.version=='critical-review-v1':
            result={'decisions':[{'index':i,'verdict':'keep','code':'K','why':'Reversal.'} for i,_ in enumerate(data['candidates'])]}
        elif prompt.version=='cross-check-v1':
            result={'decisions':[{'index':i,'verdict':'absent','finding':None,'why':'Correct translation.'} for i,_ in enumerate(data['candidates'])]}
        elif prompt.version=='inventory-v1':
            result={'units':[{'id':0,'source_excerpt':'الصدق فضيلة','meaning':'Truth is a virtue.'}]}
        else:
            result={'units':[{'id':0,'status':'conveyed' if data['translation']=='Truth is a virtue.' else 'partial',
                       'quote':data['translation'],'why':'Meaning checked.'}]}
        return LlmResult(json.dumps(result),config.model,{'prompt_tokens':10,'completion_tokens':10,'cost':.001},Decimal('.001'),{'response':result})


def run(tmp_path,judge=None,scope=None,run_id='test-run'):
    return run_comparison(scope or sample(),JudgeConfig(),judge or FakeJudge(),
        BudgetLedger(tmp_path,total_usd=Decimal('3'),per_run_usd=Decimal('1')),
        RunRepository(tmp_path),run_id=run_id,code_sha='a'*40,
        translator_vendors={'a':None,'b':'anthropic'})


def test_full_symmetric_protocol_manifest_and_immutable_replay(tmp_path):
    judge=FakeJudge(); report=run(tmp_path,judge)
    assert report['status']=='completed'
    assert report['scores']['a']['K']==1 and report['scores']['b']['K']==0
    assert sum(p.version=='assessment-v1' for p in judge.calls)==6
    assert sum(p.version=='coverage-v1' for p in judge.calls)==4
    assert sum(p.version=='critical-review-v1' for p in judge.calls)==1
    assert sum(p.version=='cross-check-v1' for p in judge.calls)==1
    assert report['manifest']['translator_independence']=={'a':'unknown','b':'same_vendor'}
    assert report['cost']['reported_usd']=='0.013000'
    assert report['manifest']['actual_models']==[JudgeConfig().model]
    assert all(c['prompt_sha256'] for c in report['calls'])
    assert RunRepository(tmp_path).get('test-run')==report
    with pytest.raises(EvaluationError): run(tmp_path,judge)
    assert len(judge.calls)==13
    assert RunRepository(tmp_path).get('test-run')==report


def test_role_swap_swaps_findings_without_bias(tmp_path):
    s=sample(); swapped=replace(s,texts=s.texts | {'a':s.texts['b'],'b':s.texts['a']},
        hashes=s.hashes | {'a':s.hashes['b'],'b':s.hashes['a']},
        ranges=s.ranges | {'a':s.ranges['b'],'b':s.ranges['a']})
    first=run(tmp_path,run_id='first'); second=run(tmp_path,scope=swapped,run_id='second')
    assert first['scores']['a']==second['scores']['b']
    assert first['scores']['b']==second['scores']['a']


def test_incomplete_or_budget_stopped_run_never_receives_scores(tmp_path):
    class Broken(FakeJudge):
        def complete(self,p,c): raise EvaluationError('truncated','Incomplete')
    report=run(tmp_path,Broken())
    assert report['status']=='failed' and report['scores'] is None
    assert Decimal(report['cost']['unresolved_reserved_usd'])>0
    assert report['error']['code']=='truncated'


def test_unconfirmed_scope_never_calls_gateway(tmp_path):
    judge=FakeJudge()
    with pytest.raises(EvaluationError): run(tmp_path,judge,replace(sample(),status='needs_review'))
    assert not judge.calls
