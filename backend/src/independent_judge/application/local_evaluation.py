"""Local background orchestration; browser disconnects never cancel a run."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, fields
import json
from independent_judge.application.judge_runner import run_comparison
from independent_judge.application.hadith_verification import verify_hadiths
from independent_judge.domain.errors import InputError
from independent_judge.domain.evaluation import JudgeConfig, EvaluationError
from independent_judge.domain.scope import PreparedComparison, text_hash
from independent_judge.evaluation_ports import JudgePort, BudgetPort, RunPort


@dataclass(frozen=True)
class EvaluationRuntime:
    config: JudgeConfig
    judge: JudgePort
    budget: BudgetPort
    reports: RunPort
    code_sha: str
    protocol: str = 'blind-3pass-exact-consensus-v1'


def reference_key(scope: dict) -> str:
    return text_hash(json.dumps({k: scope.get(k) for k in
        ('hashes', 'profile', 'source_language', 'target_language')}, sort_keys=True))


class LocalEvaluation:
    def __init__(self, scopes, jobs, library, runtime: EvaluationRuntime | None, official=None):
        self.scopes, self.jobs, self.library, self.runtime = scopes, jobs, library, runtime
        self.official = official
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='local-judge')

    def start(self):
        self.jobs.activate()

    def close(self):
        self.executor.shutdown(wait=True)
        self.jobs.close()

    def references(self, scope: dict) -> dict:
        result = verify_hadiths(scope['texts'], self.library, self.official)
        self.jobs.save_reference(reference_key(scope), result)
        return result

    def submit(self, scope_id: str) -> dict:
        scope = self.scopes.get(scope_id)
        if scope is None: raise InputError('scope_not_found', 'Материалы не найдены.')
        if scope['status'] != 'ready':
            raise InputError('unconfirmed_scope', 'Подтвердите совпадение границ трёх материалов.')
        existing = self.jobs.get(scope_id)
        if existing['id']: return self.status(scope_id)
        if not self.runtime:
            raise InputError('judge_disabled', 'Живой судья не настроен: нужны настройки модели и утверждённый бюджет оператора.')
        job, inserted = self.jobs.claim(scope_id)
        if inserted: self.executor.submit(self._execute, scope_id, scope, job['id'])
        return {k: v for k, v in job.items() if k != 'report'}

    def status(self, scope_id: str) -> dict:
        if self.scopes.get(scope_id) is None: raise InputError('scope_not_found', 'Материалы не найдены.')
        return {k: v for k, v in self.jobs.get(scope_id).items() if k != 'report'}

    def _execute(self, scope_id: str, stored: dict, run_id: str):
        self.jobs.update(scope_id, 'running')
        try:
            scope = PreparedComparison(**{f.name: stored[f.name] for f in fields(PreparedComparison)})
            runtime = self.runtime
            report = run_comparison(scope, runtime.config, runtime.judge, runtime.budget,
                                    runtime.reports, run_id=run_id, code_sha=runtime.code_sha,
                                    protocol=runtime.protocol)
            self.jobs.update(scope_id, 'checking_references', report=report,
                             error=report.get('error', {}).get('code'))
            if scope.profile == 'islamic-scholarly':
                self.references(stored)
            else:
                self.jobs.save_reference(reference_key(stored), {
                    'status': 'not_requested', 'items': [], 'verified_count': None,
                    'translation_accuracy': 'not_assessed', 'detection': 'profile_not_requested'})
            self.jobs.update(scope_id, report['status'], report=report,
                             error=report.get('error', {}).get('code'))
        except EvaluationError as exc:
            self.jobs.update(scope_id, 'failed', error=exc.code)
        except Exception:
            # Persist terminal state; never expose private payloads or replay calls.
            saved = self.jobs.get(scope_id)['report']
            if saved:
                self.jobs.update(scope_id, saved['status'], report=saved,
                                 error='reference_check_failed')
            else:
                self.jobs.update(scope_id, 'failed', error='local_run_failed')
