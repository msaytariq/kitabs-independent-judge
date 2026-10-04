"""Project saved protocol evidence into counts, never into unreviewed facts."""
from collections import defaultdict
import json
from independent_judge.domain.errors import InputError
from independent_judge.domain.evidence import anchor_finding
from independent_judge.domain.scope import text_hash
from independent_judge.domain.scoring import counts


def finding_id(side: str, finding: dict) -> str:
    return text_hash(json.dumps([side, finding['source_excerpt'], finding['current_text']],
                                ensure_ascii=False))[:24]


def validate_scope(scope: dict) -> None:
    if any(text_hash(scope['texts'][role]) != scope['hashes'][role] for role in ('source', 'a', 'b')):
        raise InputError('stale_scope', 'Текст не соответствует сохранённому хэшу.')


def _findings(record: dict) -> list[dict]:
    scope, run = record['scope'], record['run']
    saved = run['manifest']['scope']
    for key in ('texts', 'hashes', 'profile', 'source_language', 'target_language'):
        if saved[key] != scope[key]:
            raise InputError('report_scope_mismatch', 'Сохранённый результат относится к другим материалам или условиям.')
    result = []
    for side in ('a', 'b'):
        groups = defaultdict(list)
        for finding in run['findings'].get(side, []):
            groups[finding_id(side, finding)].append(finding)
        for key, variants in groups.items():
            finding = variants[0]
            codes = {v['code'] for v in variants}
            if not codes <= set('KTAS'):
                raise InputError('invalid_finding_code', 'Неизвестная категория находки.')
            anchored = anchor_finding(finding, scope['texts']['source'], scope['texts'][side])
            annotation = record.get('annotations', {}).get(key, {})
            conflict = len(codes) != 1
            status = 'disputed' if conflict or annotation.get('status') == 'disputed' else 'unreviewed'
            if anchored['evidence_status'] != 'verified': status = 'unlocated'
            result.append({**anchored, 'id': key, 'side': side,
                           'code': finding['code'] if not conflict else '?',
                           'classification_conflict': conflict, 'status': status,
                           'why_ru': annotation.get('why_ru'),
                           'review_note_ru': annotation.get('review_note_ru'),
                           'repeated': any(v.get('repeated', False) for v in variants)})
    return result


def summarize_comparison(record: dict) -> dict:
    scope, run = record['scope'], record.get('run')
    validate_scope(scope)
    findings = _findings(record) if run else []
    measured = bool(run and run.get('status') in ('completed', 'needs_review'))
    source_chars = len(scope['texts']['source'])
    sides = {}
    for side in ('a', 'b'):
        all_items = [f for f in findings if f['side'] == side]
        located = [f for f in all_items if f['status'] != 'unlocated']
        by_code = counts(located)
        sides[side] = {
            'candidates': len(located) if measured else None,
            'text_candidates': sum(f['code'] in 'KTS' for f in located) if measured else None,
            'apparatus_candidates': by_code['A'] if measured else None,
            'by_code': by_code if measured else None,
            'disputed': sum(f['status'] == 'disputed' for f in located),
            'unlocated': len(all_items) - len(located),
            'classification_conflicts': sum(f['classification_conflict'] for f in located),
            'repeated': sum(f['repeated'] for f in located),
            # Quote verification and model appeals are not human adjudication.
            'necessary_edits': None,
        }
    return {'source_chars': source_chars, 'source_pages': round(source_chars / 1800, 2),
            'negotiation_grade': source_chars >= 5400,
            'measured': measured, 'sides': sides, 'findings': findings,
            'counting_version': 'unique-final-quote-pairs-v1'}
