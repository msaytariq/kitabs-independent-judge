"""Execution measurements, never estimates from judge findings or decisions."""
import math
import re

VERSION = 'applied-processing-5s-v1'
_IDENTITY = ('job_id', 'chunk_id', 'stage', 'artifact_id', 'artifact_sha256', 'edit_id')


def _duration(packet: dict) -> float | None:
    intervals = packet.get('intervals')
    if packet.get('timing_complete') is not True or not isinstance(intervals, list) or not intervals:
        return None
    spans = []
    for span in intervals:
        if not isinstance(span, dict):
            return None
        start, end = span.get('start'), span.get('end')
        if (any(type(v) not in (int, float) or not math.isfinite(v) for v in (start, end))
                or start < 0 or end < start):
            return None
        spans.append((start, end))
    # Union includes retries; overlapping execution intervals count once.
    start, end = sorted(spans)[0]
    total = 0
    for following, finish in sorted(spans)[1:]:
        if following > end:
            total += end - start
            start, end = following, finish
        else:
            end = max(end, finish)
    return round(total + end - start, 6)


def _operations(packet: dict) -> list[dict] | None:
    events = packet.get('operations')
    if packet.get('operations_complete') is not True or not isinstance(events, list):
        return None
    unique = {}
    for event in events:
        if not isinstance(event, dict) or any(not isinstance(event.get(k), str) or not event[k] for k in _IDENTITY):
            return None
        if event['job_id'] != packet['job_id'] or event['stage'] not in ('audit', 'editor', 'proofreader'):
            return None
        key = tuple(event[k] for k in _IDENTITY)
        if key in unique and unique[key] != event:
            return None
        unique[key] = event
    result = []
    for event in unique.values():
        if event.get('status') in ('accepted', 'rejected', 'pending', 'unapplied'):
            continue
        if event.get('status') != 'applied' or event.get('execution_confirmed') is not True:
            return None
        if any(not isinstance(event.get(k), str) for k in ('before', 'after')):
            return None
        if any(not re.fullmatch('[0-9a-f]{64}', str(event.get(k, ''))) for k in
               ('input_sha256', 'output_sha256', 'receipt_sha256', 'artifact_sha256')):
            return None
        if event['before'] == event['after'] or event['input_sha256'] == event['output_sha256']:
            continue
        if event['stage'] in ('audit', 'editor'):
            result.append(event)
    return result


def processing_effort(record: dict) -> dict:
    sides = {}
    for side in ('a', 'b'):
        result = {'pipeline_seconds': None, 'audit_operations': None, 'editor_operations': None,
                  'simulated_seconds': None, 'total_seconds': None, 'operations': [],
                  'reason': 'time_not_established', 'job_id': None}
        packet = (record.get('processing') or {}).get(side)
        hashes = record['scope']['hashes']
        if (isinstance(packet, dict) and packet.get('job_id') and packet.get('state') == 'completed'
                and packet.get('source_sha256') == hashes['source']
                and packet.get('text_sha256') == hashes[side]):
            duration, operations = _duration(packet), _operations(packet)
            result.update(pipeline_seconds=duration, job_id=packet['job_id'], reason='incomplete_measurement')
            if operations is not None:
                audit = sum(e['stage'] == 'audit' for e in operations)
                editor = sum(e['stage'] == 'editor' for e in operations)
                result.update(audit_operations=audit, editor_operations=editor,
                              simulated_seconds=5 * (audit + editor), operations=operations)
                if duration is not None:
                    result.update(total_seconds=duration + 5 * (audit + editor), reason=None)
        sides[side] = result
    return {'version': VERSION, 'seconds_per_operation': 5, 'human_participation': 'simulated', 'sides': sides}
