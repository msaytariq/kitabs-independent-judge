"""One admitted judge call that finds each verse and hadith of the original in A and B."""
from dataclasses import asdict
from datetime import datetime, timezone
from independent_judge.application.run_admission import AdmittedCalls
from independent_judge.domain.evaluation import EvaluationError
from independent_judge.domain.reference_coverage import coverage_prompt, parse_coverage, VERSION
from independent_judge.domain.run_manifest import identity, digest
from independent_judge.domain.scope import text_hash


def assess_coverage(scope, call) -> dict:
    return parse_coverage(call('coverage-0', coverage_prompt(scope.texts)), scope.texts)


def run_coverage(scope, config, judge, budget, repository, *, run_id, code_sha, on_progress=None):
    if scope.status != 'ready' or any(text_hash(t) != scope.hashes.get(k) for k, t in scope.texts.items()):
        raise EvaluationError('stale_scope', 'Text hashes differ from the selected scope.')
    prompt = coverage_prompt(scope.texts)
    templates = {'0': digest(asdict(prompt))}
    manifest = {'identity': identity(scope, config, code_sha, templates), 'code_sha': code_sha,
                'scope': asdict(scope), 'config': asdict(config), 'prompt_templates': templates,
                'protocol_version': VERSION, 'started_at': datetime.now(timezone.utc).isoformat()}
    repository.begin(run_id, manifest)
    call = AdmittedCalls(judge, budget, repository, run_id, config, on_progress)
    report = {'id': run_id, 'manifest': manifest, 'status': 'running', 'coverage': None}
    try:
        report['coverage'] = assess_coverage(scope, call)
        report['status'] = 'completed'
    except EvaluationError as exc:
        report['status'] = 'budget_stopped' if exc.code == 'budget_exceeded' else 'failed'
        report['error'] = {'code': exc.code, 'message': str(exc)}
    manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
    manifest['actual_models'] = sorted({c['actual_model'] for c in call.calls if c.get('actual_model')})
    report.update(calls=call.calls, cost=budget.summary(run_id))
    repository.finish(run_id, report)
    return report
