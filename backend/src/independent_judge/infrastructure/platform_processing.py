"""Build the processing journal of a completed Kitabs autopilot job from its own records.

An "accepted" review status is a claim. An operation counts as applied only when the
stage input contains the quoted text and the text handed to the next stage contains
the replacement. Any accepted edit that cannot be confirmed makes the journal
incomplete, so the time stays unknown instead of becoming a smaller number.
"""
import hashlib
import json
from independent_judge.domain.scope import text_hash

# Stage -> (artifact kind, input field, next stage kind, next stage input field).
_FLOW = {'audit': ('audit_report', 'translatedText', 'edited_chunk', 'inputText'),
         'editor': ('edited_chunk', 'inputText', 'proofread_chunk', 'inputText')}


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _operations(job_id: str, artifacts: list[dict], reviews: list[dict]) -> list[dict] | None:
    by_kind = {}
    for item in artifacts:
        if item.get('jobId') != job_id:
            continue
        key = (item['kind'], item.get('chunkId'))
        if key in by_kind:
            return None
        by_kind[key] = item
    statuses = {(r['stage_id'], r['chunk_id'], int(r['issue_index'])): r for r in reviews}
    chunks = sorted({chunk for kind, chunk in by_kind if kind == 'audit_report'}
                    | {chunk for kind, chunk in by_kind if kind == 'edited_chunk'})
    if not chunks:
        return None
    operations = []
    for stage, (kind, input_field, next_kind, next_field) in _FLOW.items():
        for chunk in chunks:
            current, following = by_kind.get((kind, chunk)), by_kind.get((next_kind, chunk))
            if current is None or following is None:
                return None
            before_text = current['payload'][input_field]
            after_text = following['payload'][next_field]
            for index, issue in enumerate(current['payload'].get('issues') or []):
                review = statuses.get((stage, chunk, index))
                if review is None:
                    return None
                old, new = issue.get('currentText') or '', issue.get('revisedText')
                status = review['status']
                if status == 'accepted':
                    if not old or not isinstance(new, str):
                        return None
                    if old != new and (old not in before_text or new not in after_text):
                        return None
                    status = 'applied'
                operations.append({
                    'job_id': job_id, 'chunk_id': chunk, 'stage': stage,
                    'artifact_id': current['id'], 'artifact_sha256': current['hash'],
                    'edit_id': str(index), 'status': status, 'execution_confirmed': status == 'applied',
                    'before': old, 'after': new if isinstance(new, str) else '',
                    'input_sha256': _sha(before_text), 'output_sha256': _sha(after_text),
                    'receipt_sha256': _sha(json.dumps(review, sort_keys=True, ensure_ascii=False))})
    return operations


def processing_packet(*, job_id: str, artifacts: list[dict], reviews: list[dict],
                      intervals: list[dict] | None, source_sha256: str, b_text: str) -> dict:
    operations = _operations(job_id, artifacts, reviews)
    return {'job_id': job_id, 'state': 'completed', 'source_sha256': source_sha256,
            'text_sha256': text_hash(b_text),
            'timing_complete': bool(intervals), 'intervals': list(intervals or []),
            'operations_complete': operations is not None, 'operations': operations or []}
