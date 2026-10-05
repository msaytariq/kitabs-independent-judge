"""Create a visibly synthetic catalog entry through the real offline protocol."""
import argparse
from dataclasses import asdict, replace
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
# This command is a test/demo tool, deliberately not a production provider.
from test_runner import FakeJudge
from test_judge_contracts import sample
from independent_judge.application.judge_runner import run_comparison
from independent_judge.domain.evaluation import JudgeConfig
from independent_judge.domain.scope import text_hash
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository


class OfflineFixture(FakeJudge):
    def complete(self, prompt, config):
        result = super().complete(prompt, config)
        return replace(result, actual_model='fixture/offline-no-model', cost_usd=Decimal('0'),
                       usage={'prompt_tokens':0,'completion_tokens':0,'cost':0})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    args = parser.parse_args()
    directory = args.data_dir.resolve()
    catalog = directory / 'comparison-catalog' / 'synthetic-demo.json'
    if catalog.exists():
        raise SystemExit('Synthetic demo already exists; no data was replaced.')
    code_sha = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    scope = replace(sample(), profile='general')
    config = JudgeConfig()
    report = run_comparison(scope, config, OfflineFixture(),
        BudgetLedger(directory, total_usd=Decimal('3'), per_run_usd=Decimal('1')),
        RunRepository(directory),run_id='synthetic-demo',code_sha=code_sha)
    if report['status'] != 'completed':
        raise SystemExit('Offline fixture failed; inspect test output.')
    data = {'id':'synthetic-demo', 'title':'Synthetic demo / Учебный пример',
            'description':'Deterministic test fixture. No live model or vendor output.',
            'demonstration':True,'scope':asdict(scope),'run':report,
            'report_sha256':text_hash(json.dumps(report,sort_keys=True,ensure_ascii=False)),
            'provenance':{'a':'Synthetic flawed sentence','b':'Synthetic corrected sentence'}}
    catalog.parent.mkdir(parents=True,exist_ok=True)
    catalog.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Created labelled offline fixture: {catalog}')


if __name__ == '__main__': main()
