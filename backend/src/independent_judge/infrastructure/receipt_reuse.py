"""Explicit continuation from exact paid receipts; no new billing for reused text."""
from collections import defaultdict, deque
from dataclasses import asdict
from decimal import Decimal
import json
import sqlite3

from independent_judge.domain.evaluation import EvaluationError, LlmResult
from independent_judge.domain.run_manifest import digest
from independent_judge.infrastructure.gateway_usage import reported_cost


class ReceiptReuseJudge:
    def __init__(self, live, database, source_run_id, config):
        self.live, self.config = live, config
        self.saved = defaultdict(deque)
        with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
            row = db.execute('SELECT request,report FROM runs WHERE id=?', (source_run_id,)).fetchone()
            if row is None or row[1] is None:
                raise EvaluationError('invalid_continuation', 'A finalized source run is required.')
            if json.loads(row[0]).get('config') != asdict(config):
                raise EvaluationError('invalid_continuation', 'Continuation must keep the exact model configuration.')
            receipts = [(call, json.loads(snapshot)) for call, snapshot in db.execute(
                'SELECT call_id,snapshot FROM receipts WHERE run_id=?', (source_run_id,))]
        for call_id, snapshot in sorted(receipts, key=lambda item: item[1]['started_at']):
            raw = snapshot.get('raw') or {}
            choices, usage = raw.get('choices', []), raw.get('usage', {})
            if (snapshot.get('error') or raw.get('model') != config.model
                    or reported_cost(raw) is None or len(choices) != 1
                    or choices[0].get('finish_reason') != 'stop'
                    or not isinstance(usage, dict)
                    or any(type(usage.get(k)) is not int or usage[k] < 0
                           for k in ('prompt_tokens', 'completion_tokens'))):
                continue
            text = choices[0].get('message', {}).get('content')
            if not isinstance(text, str) or not text.strip(): continue
            reused = {'run_id': source_run_id, 'call_id': call_id,
                      'receipt_sha256': digest(snapshot), 'original_cost_usd': str(reported_cost(raw))}
            result = LlmResult(text, raw['model'], {'prompt_tokens': 0, 'completion_tokens': 0,
                'reused': True}, Decimal('0'), {'reused_from': reused, 'original_response': raw})
            self.saved[digest(snapshot['prompt'])].append(result)

    def complete(self, prompt, config):
        if config != self.config:
            raise EvaluationError('invalid_continuation', 'Continuation configuration changed.')
        queue = self.saved[digest(asdict(prompt))]
        return queue.popleft() if queue else self.live.complete(prompt, config)
