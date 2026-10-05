"""Two ordered assessments with persistent budget admission and immutable receipts."""
from dataclasses import asdict
from datetime import datetime, timezone
import re
from independent_judge.application.run_admission import AdmittedCalls
from independent_judge.application.paired_disputes import examine_disputes
from independent_judge.domain.evaluation import EvaluationError
from independent_judge.domain.paired_rubric import paired_prompt, VERSION
from independent_judge.domain.paired_assessment import parse_assessment
from independent_judge.domain.paired_consensus import reconcile_assessments
from independent_judge.domain.structural_checks import structural_checks
from independent_judge.domain.run_manifest import identity, independence, digest
from independent_judge.domain.scope import text_hash


def run_paired(scope, config, judge, budget, repository, *, run_id, code_sha,
               translator_vendors=None, on_progress=None):
    if scope.status != 'ready':
        raise EvaluationError('unconfirmed_scope', 'Confirm matching source ranges first.')
    if not re.fullmatch('[0-9a-f]{40}', code_sha):
        raise EvaluationError('invalid_code_sha', 'A complete Git checkpoint is required.')
    if set(scope.texts) != {'source', 'a', 'b'} or any(text_hash(t) != scope.hashes.get(k) for k, t in scope.texts.items()):
        raise EvaluationError('stale_scope', 'Text hashes differ from the selected scope.')
    prompts = [paired_prompt(scope, order) for order in (('a', 'b'), ('b', 'a'))]
    template_hashes = {str(n): digest(asdict(p)) for n, p in enumerate(prompts)}
    vendors = translator_vendors or {}
    manifest = {'identity': identity(scope, config, code_sha, template_hashes), 'code_sha': code_sha,
                'scope': asdict(scope), 'config': asdict(config), 'prompt_templates': template_hashes,
                'protocol_version': VERSION, 'scoring_version': VERSION,
                'effective_parameters': {'max_tokens': config.max_tokens, 'reasoning_effort': config.reasoning_effort,
                    'requested_temperature': config.temperature, 'temperature_sent': False,
                    'temperature_note': 'Unsupported by catalog' if config.temperature is not None else 'Not requested'},
                'translator_independence': {s: independence(config.model, vendors.get(s)) for s in ('a', 'b')},
                'started_at': datetime.now(timezone.utc).isoformat()}
    repository.begin(run_id, manifest)
    call = AdmittedCalls(judge, budget, repository, run_id, config, on_progress)
    report = {'id': run_id, 'manifest': manifest, 'status': 'running', 'scores': None,
              'passes': [], 'paired': None, 'findings': {}, 'structural': structural_checks(scope.texts),
              'limitations': ['Machine assessment of this selected material only.',
                              'External references not checked; vendor chunk boundaries unknown.',
                              'Two orders of one model are not an independent panel.']}
    try:
        for n, order in enumerate((('a', 'b'), ('b', 'a'))):
            answer = call(f'paired-{n}', prompts[n])
            report['passes'].append(parse_assessment(answer, scope, order))
        report['paired'] = reconcile_assessments(report['passes'], scope)
        report['adjudication'] = examine_disputes(scope, report['paired'], call)
        report['status'] = 'completed'
    except EvaluationError as exc:
        report['status'] = 'budget_stopped' if exc.code == 'budget_exceeded' else 'failed'
        report['error'] = {'code': exc.code, 'message': str(exc)}
    manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
    manifest['actual_models'] = sorted({c['actual_model'] for c in call.calls if c.get('actual_model')})
    report.update(calls=call.calls, cost=budget.summary(run_id))
    repository.finish(run_id, report)
    return report
