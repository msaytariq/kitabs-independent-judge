"""Local background orchestration; browser disconnects never cancel a run."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, fields
import json
from independent_judge.application.judge_runner import run_comparison
from threading import Lock
from independent_judge.application.reference_verification import verify_references
from independent_judge.application.sunnah_verification import verify_official
from independent_judge.domain.hadith_matching import HadithIndex
from independent_judge.domain.quran_matching import QuranIndex
from independent_judge.reference_ports import LibraryUnavailable
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
    # A judge of another family grades the same criteria (bias check); None keeps one judge.
    second_config: JudgeConfig | None = None


def reference_key(scope: dict) -> str:
    return text_hash(json.dumps({k: scope.get(k) for k in
        ('hashes', 'profile', 'source_language', 'target_language')}, sort_keys=True))


class LocalEvaluation:
    def __init__(self, scopes, jobs, library, runtime: EvaluationRuntime | None, official=None, quran=None):
        self.scopes, self.jobs, self.library, self.runtime = scopes, jobs, library, runtime
        self.official, self.quran = official, quran
        self.index_lock, self.indexes = Lock(), None
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='local-judge')

    def start(self):
        self.jobs.activate()

    def close(self):
        self.executor.shutdown(wait=True)
        self.jobs.close()

    def _reference_indexes(self):
        # Built once per process: about 35,000 hadith records and 6,236 verses.
        if self.library is None or self.quran is None:
            raise LibraryUnavailable('Reference libraries are not configured')
        with self.index_lock:
            if self.indexes is None:
                self.indexes = (QuranIndex(self.quran.verses()), HadithIndex(self.library.records()))
            return self.indexes

    def references(self, scope: dict) -> dict:
        try:
            quran, hadith = self._reference_indexes()
        except LibraryUnavailable:
            quran = hadith = None
        result = verify_references(scope['texts'], self.quran, self.library, quran_index=quran, hadith_index=hadith)
        if result['status'] == 'checked':
            result['official'] = verify_official(result['hadith']['items'], self.official)
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

    def _second_judge(self, scope, run_id: str) -> dict | None:
        """The second judge's grades; a response off the schema gets one more own run, never the first's."""
        runtime = self.runtime
        for attempt in ('', '-retry'):
            second_id = f'{run_id}-second{attempt}'
            report = run_comparison(scope, runtime.second_config, runtime.judge, runtime.budget, runtime.reports,
                                    run_id=second_id, code_sha=runtime.code_sha, protocol=runtime.protocol)
            if report['status'] == 'completed' and report.get('rubric'):
                return {'model': ', '.join(report['manifest'].get('actual_models', [])), 'run_id': second_id,
                        'rubric': report['rubric'], 'cost': report.get('cost')}
            if report['status'] == 'budget_stopped':
                return None
        return None

    def _execute(self, scope_id: str, stored: dict, run_id: str):
        self.jobs.update(scope_id, 'running')
        try:
            scope = PreparedComparison(**{f.name: stored[f.name] for f in fields(PreparedComparison)})
            runtime = self.runtime
            report = run_comparison(scope, runtime.config, runtime.judge, runtime.budget,
                                    runtime.reports, run_id=run_id, code_sha=runtime.code_sha,
                                    protocol=runtime.protocol)
            if report['status'] == 'completed' and runtime.second_config is not None:
                report = report | {'second_judge': self._second_judge(scope, run_id)}
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
