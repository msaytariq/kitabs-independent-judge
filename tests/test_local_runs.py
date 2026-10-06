"""New materials use the real protocol; provider only is deterministic offline."""
from decimal import Decimal
import time
from fastapi.testclient import TestClient
from independent_judge.api.app import create_app
from independent_judge.domain.evaluation import JudgeConfig
from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.run_repository import RunRepository
from test_runner import FakeJudge


def prepare(client, confirmed=True):
    draft = client.post('/api/comparisons/text', json={
        'source': 'الصدق فضيلة', 'a': 'Truth is a vice.', 'b': 'Truth is a virtue.',
        'source_language': 'ar', 'target_language': 'en'}).json()
    return client.post(f"/api/comparisons/{draft['id']}/scopes", json={
        'confirmed': confirmed, 'profile': 'general', 'ranges': {
            k: {'start': 0, 'end': len(v['text']), 'text_sha256': v['sha256']}
            for k, v in draft['materials'].items()}}).json()['id']


def runtime(tmp_path, judge):
    from independent_judge.application.local_evaluation import EvaluationRuntime
    return EvaluationRuntime(JudgeConfig(), judge,
        BudgetLedger(tmp_path, total_usd=Decimal('3'), per_run_usd=Decimal('1')),
        RunRepository(tmp_path), 'a' * 40)


def wait_done(client, scope):
    for _ in range(100):
        state = client.get(f'/api/scopes/{scope}/run').json()
        if state['status'] not in ('queued', 'running', 'checking_references'): return state
        time.sleep(.01)
    raise AssertionError('Run did not finish')


def test_disabled_run_does_not_start_or_invent_results(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        scope = prepare(client)
        response = client.post(f'/api/scopes/{scope}/run')
        assert response.status_code == 409
        assert response.json()['error']['code'] == 'judge_disabled'
        assert client.get(f'/api/scopes/{scope}/comparison').json()['effort']['reduction_percent'] is None
    assert not (tmp_path / 'budget.sqlite3').exists()


def test_new_scope_runs_once_and_result_survives_reload(tmp_path):
    judge = FakeJudge()
    app = create_app(tmp_path, evaluation=runtime(tmp_path, judge))
    with TestClient(app) as client:
        scope = prepare(client)
        first = client.post(f'/api/scopes/{scope}/run')
        assert first.status_code == 202
        assert client.post(f'/api/scopes/{scope}/run').json()['id'] == first.json()['id']
        assert wait_done(client, scope)['status'] == 'completed'
        view = client.get(f'/api/scopes/{scope}/comparison').json()
        assert view['summary']['sides']['a']['candidates'] == 1
        assert view['effort']['reduction_percent'] == 100
        assert view['hadith']['status'] == 'not_requested'
        assert 'manual' not in view['effort']
        call_count = len(judge.calls)
        client.post(f'/api/scopes/{scope}/run')
        assert len(judge.calls) == call_count
    with TestClient(create_app(tmp_path)) as client:
        view = client.get(f'/api/scopes/{scope}/comparison').json()
        assert view['run']['id'] == first.json()['id']
        assert view['summary']['sides']['a']['candidates'] == 1
        assert client.get(f'/api/scopes/{scope}/report.html').status_code == 200


def test_unconfirmed_scope_never_enters_model_queue(tmp_path):
    judge = FakeJudge()
    with TestClient(create_app(tmp_path, evaluation=runtime(tmp_path, judge))) as client:
        scope = prepare(client, confirmed=False)
        assert client.post(f'/api/scopes/{scope}/run').status_code == 422
        assert judge.calls == []


def test_failed_provider_stays_failed_on_repeated_click(tmp_path):
    from independent_judge.domain.evaluation import EvaluationError
    class Broken(FakeJudge):
        def complete(self, prompt, config):
            self.calls.append(prompt)
            raise EvaluationError('gateway_transport', 'Offline failure')
    judge = Broken()
    with TestClient(create_app(tmp_path, evaluation=runtime(tmp_path, judge))) as client:
        scope = prepare(client)
        client.post(f'/api/scopes/{scope}/run')
        assert wait_done(client, scope)['status'] == 'failed'
        client.post(f'/api/scopes/{scope}/run')
        assert len(judge.calls) == 1
        view = client.get(f'/api/scopes/{scope}/comparison').json()
        assert view['effort']['reduction_percent'] is None


def test_restart_without_live_recovers_finished_report_and_interrupts_orphan(tmp_path):
    from independent_judge.infrastructure.local_jobs import LocalJobs
    from independent_judge.application.judge_runner import run_comparison
    from independent_judge.bootstrap import build_scope
    from independent_judge.domain.scope import PreparedComparison
    from dataclasses import fields
    with TestClient(create_app(tmp_path)) as client:
        ready, orphan = prepare(client), prepare(client)
    jobs = LocalJobs(tmp_path)
    job, _ = jobs.claim(ready); jobs.update(ready, 'running')
    jobs.claim(orphan)
    stored = build_scope(tmp_path).get(ready)
    scope = PreparedComparison(**{f.name: stored[f.name] for f in fields(PreparedComparison)})
    rt = runtime(tmp_path, FakeJudge())
    run_comparison(scope, rt.config, rt.judge, rt.budget, rt.reports,
                   run_id=job['id'], code_sha=rt.code_sha)
    with TestClient(create_app(tmp_path)) as client:
        assert client.get(f'/api/scopes/{ready}/run').json()['status'] == 'completed'
        assert client.get(f'/api/scopes/{ready}/comparison').json()['summary']['measured']
        assert client.get(f'/api/scopes/{orphan}/run').json()['status'] == 'interrupted'


def test_reference_identity_separates_profiles_and_language():
    from independent_judge.application.local_evaluation import reference_key
    scope = {'hashes': {'source': 'x', 'a': 'y', 'b': 'z'}, 'profile': 'general',
             'source_language': 'ar', 'target_language': 'en'}
    assert reference_key(scope) != reference_key(scope | {'profile': 'islamic-scholarly'})
    assert reference_key(scope) != reference_key(scope | {'target_language': 'ru'})


def test_finished_judge_is_persisted_while_references_are_pending(tmp_path):
    from threading import Event
    from independent_judge.application.local_evaluation import LocalEvaluation
    from independent_judge.infrastructure.local_jobs import LocalJobs
    from independent_judge.bootstrap import build_scope
    entered, release = Event(), Event()
    with TestClient(create_app(tmp_path)) as client:
        scope_id = prepare(client)
    scopes, jobs = build_scope(tmp_path), LocalJobs(tmp_path)
    stored = scopes.get(scope_id) | {'profile': 'islamic-scholarly'}
    runner = LocalEvaluation(scopes, jobs, None, runtime(tmp_path, FakeJudge()))
    def slow_references(scope):
        entered.set()
        assert release.wait(5)
    runner.references = slow_references
    job, _ = jobs.claim(scope_id)
    future = runner.executor.submit(runner._execute, scope_id, stored, job['id'])
    try:
        assert entered.wait(5)
        pending = jobs.get(scope_id)
        assert pending['report']['status'] == 'completed'
        assert pending['status'] == 'checking_references'
    finally:
        release.set(); future.result(); runner.close()
    assert jobs.get(scope_id)['status'] == 'completed'


def test_a_live_run_adds_the_second_judge_of_another_family(tmp_path):
    from pathlib import Path
    from independent_judge.application.local_evaluation import EvaluationRuntime
    from independent_judge.operator_config import load_judge_config
    from test_rubric_comparison import Judge
    judge = Judge()
    first = JudgeConfig()
    grok = load_judge_config(Path(__file__).parents[1] / 'config' / 'judge-grok-4.1-fast.json')
    rt = EvaluationRuntime(first, judge, BudgetLedger(tmp_path, total_usd=Decimal('3'), per_run_usd=Decimal('1')),
                           RunRepository(tmp_path), 'a' * 40, protocol='rubric-v1',
                           second_config=grok)
    with TestClient(create_app(tmp_path, evaluation=rt)) as client:
        scope = prepare(client)
        client.post(f'/api/scopes/{scope}/run')
        assert wait_done(client, scope)['status'] == 'completed'
        view = client.get(f'/api/scopes/{scope}/comparison').json()
    second = view['second_judge']
    assert second['second']['model'] == grok.model and second['agree'] is True
    assert len(judge.calls) == 4  # rubric and coverage of each judge
