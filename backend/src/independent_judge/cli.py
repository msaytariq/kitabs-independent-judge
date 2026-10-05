"""Operator-only CLI for the bounded pilot. No public paid-run endpoint yet."""
import argparse
from dataclasses import fields
from decimal import Decimal,InvalidOperation
import json
import os
import re
from pathlib import Path
import subprocess
from independent_judge.bootstrap import build_scope,data_directory
from independent_judge.domain.scope import PreparedComparison
from independent_judge.domain.evaluation import EvaluationError
from independent_judge.operator_config import load_judge_config
from independent_judge.domain.judge_prompt import assessment_prompt
from independent_judge.domain.paired_rubric import paired_prompt
from independent_judge.domain.budget import reservation
from independent_judge.application.judge_runner import run_comparison
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository
from independent_judge.infrastructure.gateway import GatewayJudge
from independent_judge.infrastructure.receipt_reuse import ReceiptReuseJudge


def code_checkpoint(repo:Path):
    def git(*args): return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
    if Path(git('rev-parse','--show-toplevel')).resolve()!=repo.resolve():
        raise EvaluationError('wrong_repo','Run from the standalone repository root.')
    if not Path(__file__).resolve().is_relative_to(repo.resolve()):
        raise EvaluationError('wrong_package','Pilot code must come from this checkout.')
    if git('status','--porcelain'):
        raise EvaluationError('dirty_code','Commit verified pilot code before a live run.')
    return git('rev-parse','HEAD')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--config',type=Path, default=os.environ.get(
        'JUDGE_CONFIG_PATH', 'config/judge-gemini-3.8-flash.json'),
        help='Explicit judge JSON configuration (or JUDGE_CONFIG_PATH).')
    parser.add_argument('--scope-id',required=True)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--reuse-run',help='Reuse exact priced receipts from a finalized local run.')
    parser.add_argument('--translator-a-vendor')
    parser.add_argument('--translator-b-vendor')
    parser.add_argument('--protocol',default='blind-3pass-exact-consensus-v1',
        choices=['blind-3pass-exact-consensus-v1','paired-rubric-v1'])
    args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",args.run_id):
        raise EvaluationError("invalid_run_id","Run ID must contain 1-80 letters, digits, underscores or hyphens.")
    directory=data_directory(args.data_dir)
    stored=build_scope(directory).get(args.scope_id)
    scope=PreparedComparison(**{f.name:stored[f.name] for f in fields(PreparedComparison)})
    config=load_judge_config(args.config)
    preflight={'scope_id':args.scope_id,'status':scope.status,'model':config.model,'protocol':args.protocol,
               'characters':{k:len(v) for k,v in scope.texts.items()}}
    if args.protocol=='paired-rubric-v1':
        # Two ordered passes plus at most one targeted dispute pass, each admitted separately.
        per_call=max(reservation(paired_prompt(scope,o),config) for o in (('a','b'),('b','a')))
        preflight|={'maximum_calls':3,'per_call_reservation_usd':str(per_call),
                    'maximum_reservation_usd':str(per_call*3)}
    else:
        preflight|={'initial_six_call_reservation_usd':str(sum(reservation(assessment_prompt(scope,s),config)*3 for s in ('a','b'))),
                    'note':'Critical review, cross-check and coverage add calls; every call is admitted separately.'}
    print(json.dumps(preflight),flush=True)
    if not args.live: return
    sha=code_checkpoint(Path.cwd())
    try:
        total=Decimal(os.environ.get('JUDGE_BUDGET_TOTAL_USD',''))
        per_run=Decimal(os.environ.get('JUDGE_BUDGET_RUN_USD',''))
    except InvalidOperation:
        raise EvaluationError('missing_budget','Set explicit total and per-run USD limits.') from None
    budget=BudgetLedger(directory,total_usd=total,per_run_usd=per_run)
    judge=GatewayJudge(os.environ.get('AI_GATEWAY_API_KEY',''))
    if args.reuse_run:
        judge=ReceiptReuseJudge(judge,directory/'runs.sqlite3',args.reuse_run,config)
    def progress(call_id,state,cost):
        print(json.dumps({'call':call_id,'state':state,'budget':cost}),flush=True)
    report=run_comparison(scope,config,judge,budget,RunRepository(directory),run_id=args.run_id,code_sha=sha,on_progress=progress,
        translator_vendors={'a':args.translator_a_vendor,'b':args.translator_b_vendor},protocol=args.protocol)
    path=directory/(args.run_id+'.json')
    # IDs accepted from an operator must not become arbitrary filesystem paths.
    if path.parent.resolve()!=directory.resolve():
        raise EvaluationError('invalid_run_id','Run ID must be a simple filename component.')
    with path.open('x') as out: json.dump(report,out,ensure_ascii=False,indent=2)
    print(json.dumps({'run_id':report['id'],'status':report['status'],'cost':report['cost'],'report':str(path)}),flush=True)


if __name__=='__main__':
    try: main()
    except EvaluationError as exc:
        print(json.dumps({'error':exc.code,'message':str(exc)}),flush=True)
        raise SystemExit(1)
