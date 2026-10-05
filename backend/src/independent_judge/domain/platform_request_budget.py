"""Conservative text-only request admission for an explicit operator rate sheet."""
from decimal import Decimal
import copy
import json

from independent_judge.domain.evaluation import EvaluationError


def bounded_request(body, rates):
    allowed = {'model', 'messages', 'temperature', 'stream', 'stream_options',
               'reasoning', 'max_tokens', 'providerOptions'}
    if not isinstance(body, dict) or set(body) - allowed:
        raise EvaluationError('unpriced_options', 'Only reviewed text completion options are admitted.')
    model = body.get('model')
    rate = rates.get(model) if isinstance(model, str) else None
    if rate is None:
        raise EvaluationError('unreviewed_model', 'Model is absent from the operator rate sheet.')
    limit = body.get('max_tokens')
    if type(limit) is not int or not 1 <= limit <= 32000:
        raise EvaluationError('pilot_bounds', 'An explicit output cap up to 32000 is required.')
    if body.get('stream') is not True or body.get('stream_options') != {'include_usage': True}:
        raise EvaluationError('missing_usage', 'Streaming usage must be requested.')
    messages = body.get('messages')
    if not isinstance(messages, list) or not messages:
        raise EvaluationError('unpriced_options', 'Text messages are required.')
    for message in messages:
        if not isinstance(message, dict) or set(message) != {'role', 'content'}:
            raise EvaluationError('unpriced_options', 'Only role/content messages are admitted.')
        content = message['content']
        if isinstance(content, str): continue
        if not isinstance(content, list) or not content:
            raise EvaluationError('unpriced_options', 'Only text content is admitted.')
        for part in content:
            if (not isinstance(part, dict) or set(part) - {'type', 'text', 'cache_control'}
                    or part.get('type') != 'text' or not isinstance(part.get('text'), str)
                    or part.get('cache_control', {'type': 'ephemeral'}) != {'type': 'ephemeral'}):
                raise EvaluationError('unpriced_options', 'Only text and five-minute caching are priced.')
    result = copy.deepcopy(body)
    options = result.setdefault('providerOptions', {})
    if not isinstance(options, dict) or set(options) - {'google', 'gateway'}:
        raise EvaluationError('unpriced_options', 'Unreviewed provider options.')
    if 'google' in options and options['google'] != {'thinkingConfig': {'thinkingBudget': 0}}:
        raise EvaluationError('unpriced_options', 'Unreviewed Google options.')
    options['gateway'] = {'only': [rate['provider']]}
    data = json.dumps(result, ensure_ascii=False).encode()
    bound = len(data) + 2048
    if bound > 100000:
        raise EvaluationError('pilot_bounds', 'Request exceeds the reviewed short-context bound.')
    input_rate, output_rate = Decimal(rate['input']), Decimal(rate['output'])
    if any(not value.is_finite() or value <= 0 for value in (input_rate, output_rate)):
        raise EvaluationError('unreviewed_price', 'Positive finite rates are required.')
    return data, (bound * input_rate + limit * output_rate) * Decimal('1.25') + Decimal('.001')
