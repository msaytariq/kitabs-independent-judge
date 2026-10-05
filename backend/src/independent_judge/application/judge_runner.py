"""Coordinate the protocol; each stage owns its policy, parsing and validation."""
from dataclasses import asdict
from datetime import datetime,timezone
import re
from independent_judge.application.run_admission import AdmittedCalls
from independent_judge.application.critical_review import review_critical
from independent_judge.application.cross_check import cross_check
from independent_judge.application.completeness import assess_completeness
from independent_judge.domain.evaluation import EvaluationError
from independent_judge.domain.judge_prompt import assessment_prompt,SYSTEM
from independent_judge.domain.critical_review_prompt import POLICY as CRITICAL
from independent_judge.domain.cross_check_prompt import POLICY as CROSS
from independent_judge.domain.completeness import INVENTORY_POLICY,COVERAGE_POLICY
from independent_judge.domain.judge_parsing import parse_findings
from independent_judge.domain.consensus import consensus
from independent_judge.domain.run_manifest import identity,independence,digest
from independent_judge.domain.profiles import profile_policy
from independent_judge.domain.scope import text_hash
from independent_judge.domain.scoring import counts,pending_review


def run_comparison(scope,config,judge,budget,repository,*,run_id,code_sha,
                   translator_vendors=None,on_progress=None,protocol='blind-3pass-exact-consensus-v1'):
    if protocol == 'rubric-v1':
        from independent_judge.application.rubric_runner import run_rubric
        return run_rubric(scope,config,judge,budget,repository,run_id=run_id,code_sha=code_sha,
                          translator_vendors=translator_vendors,on_progress=on_progress)
    if protocol != 'blind-3pass-exact-consensus-v1':
        raise EvaluationError('unknown_protocol', 'Select a versioned comparison protocol.')
    if scope.status!='ready': raise EvaluationError('unconfirmed_scope','Confirm all three ranges first.')
    if not re.fullmatch('[0-9a-f]{40}',code_sha): raise EvaluationError('invalid_code_sha','Full verified Git SHA required.')
    if any(text_hash(t)!=scope.hashes.get(k) for k,t in scope.texts.items()):
        raise EvaluationError('stale_scope','Selected text no longer matches scope hashes.')
    vendors=translator_vendors or {}
    prompts={k:digest(v) for k,v in {'assessment':SYSTEM,'critical':CRITICAL,'cross':CROSS,
        'inventory':INVENTORY_POLICY,'coverage':COVERAGE_POLICY,'profile':profile_policy(scope.profile)}.items()}
    manifest={'identity':identity(scope,config,code_sha,prompts),'code_sha':code_sha,
        'scope':asdict(scope),'config':asdict(config),'prompt_templates':prompts,
        'protocol_version':'blind-3pass-exact-consensus-v1','scoring_version':'separate-counts-v1',
        'translator_independence':{s:independence(config.model,vendors.get(s)) for s in ('a','b')},
        'started_at':datetime.now(timezone.utc).isoformat()}
    repository.begin(run_id,manifest)
    call=AdmittedCalls(judge,budget,repository,run_id,config,on_progress)
    report={'id':run_id,'manifest':manifest,'status':'running','scores':None,'passes':{},
            'findings':{},'critical_reviews':{},'cross_checks':{},'completeness':None,
            'limitations':['Machine assessment requires subject-expert review.',
                'A short selected passage cannot establish whole-book or platform superiority.',
                'Reference-library verification is not enabled.',
                'Exact-quote consensus can miss equivalent findings phrased with different quotes.']}
    try:
        for side in ('a','b'):
            report['passes'][side]=[]
            for n in range(3):
                text=call(f'assess-{n}-{side}',assessment_prompt(scope,side))
                report['passes'][side].append(parse_findings(text,scope.texts['source'],scope.texts[side]))
        for side in ('a','b'):
            found=consensus(report['passes'][side])
            report['findings'][side],report['critical_reviews'][side]=review_critical(scope,side,found,call)
        for side,other in (('a','b'),('b','a')):
            report['cross_checks'][side]=cross_check(scope,side,report['findings'][other],call)
        report['completeness']=assess_completeness(scope,call)
        report['scores']={s:counts(report['findings'][s]) for s in ('a','b')}
        report['status']='needs_review' if pending_review(report['passes'],report['cross_checks'],report['completeness']) else 'completed'
    except EvaluationError as exc:
        report['status']='budget_stopped' if exc.code=='budget_exceeded' else 'failed'
        report['error']={'code':exc.code,'message':str(exc)}
    manifest['finished_at']=datetime.now(timezone.utc).isoformat()
    manifest['actual_models']=sorted({c['actual_model'] for c in call.calls if c.get('actual_model')})
    report.update(calls=call.calls,cost=budget.summary(run_id))
    repository.finish(run_id,report)
    return report
