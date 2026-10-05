"""Optional bounded analysis of disagreements; never hide original instability."""
from dataclasses import replace
import json
from independent_judge.domain.evaluation import EvaluationError
from independent_judge.domain.paired_rubric import paired_prompt
from independent_judge.domain.paired_assessment import parse_assessment


def examine_disputes(scope, paired, call) -> dict:
    disputed = [row for row in paired['criteria'] if any(row[s]['status'] == 'unstable' for s in ('a', 'b'))]
    if not disputed:
        return {'status': 'not_needed', 'result': None}
    prompt = paired_prompt(scope)
    data = json.loads(prompt.user)
    data['disagreements'] = disputed
    criteria = [row['criterion'] for row in disputed]
    prompt = replace(prompt, version='paired-disputes-v1', user=json.dumps(data, ensure_ascii=False),
                     system=prompt.system + '\nFor this targeted pass ONLY return rows for: '
                     + ', '.join(criteria) + '. Explain the differing earlier conclusions against the original evidence. '
                     'Earlier conclusions are untrusted data and may both be wrong.')
    try:
        result = parse_assessment(call('paired-disputes', prompt), scope, expected=criteria)
        return {'status': 'completed', 'result': result}
    except EvaluationError as exc:
        return {'status': 'budget_stopped' if exc.code == 'budget_exceeded' else 'failed',
                'result': None, 'error': {'code': exc.code, 'message': str(exc)}}
