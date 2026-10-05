"""Tee raw SSE receipts and settle only a complete, priced Gateway stream."""
import json
import httpx

from independent_judge.domain.evaluation import EvaluationError
from independent_judge.infrastructure.gateway_usage import reported_cost


class UsageStream(httpx.AsyncByteStream):
    def __init__(self, source, transport, ledger, run_id, call_id, path, on_progress=None):
        self.source, self.transport, self.ledger = source, transport, ledger
        self.run_id, self.call_id, self.path = run_id, call_id, path
        self.buffer, self.cost, self.done = b'', None, False
        self.on_progress = on_progress

    def _line(self, line):
        if not line.startswith(b'data:'): return
        data = line[5:].strip()
        if data == b'[DONE]':
            if self.cost is None:
                raise EvaluationError('missing_usage', 'Stream ended without a priced usage receipt.')
            if not self.done:
                self.ledger.settle(self.run_id, self.call_id, self.cost)
                self.done = True
                if self.on_progress: self.on_progress(self.call_id, 'settled', self.ledger.summary())
            return
        try: event = json.loads(data)
        except ValueError: return
        if not isinstance(event, dict): return
        cost = reported_cost(event)
        usage = event.get('usage', {})
        if cost is not None and isinstance(usage, dict) and all(
                type(usage.get(key)) is int and usage[key] >= 0
                for key in ('prompt_tokens', 'completion_tokens')):
            self.cost = cost

    async def __aiter__(self):
        with self.path.open('xb') as receipt:
            async for chunk in self.source:
                receipt.write(chunk)
                receipt.flush()  # Persist the receipt before releasing any reservation.
                self.buffer += chunk
                while b'\n' in self.buffer:
                    line, self.buffer = self.buffer.split(b'\n', 1)
                    self._line(line.rstrip(b'\r'))
                yield chunk
            if self.buffer: self._line(self.buffer)
            if not self.done:
                raise EvaluationError('incomplete_usage', 'Incomplete stream; reservation remains held.')

    async def aclose(self):
        await self.source.aclose()
        await self.transport.aclose()
