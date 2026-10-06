"""Strict judge response parsing and exact quote location."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from independent_judge.domain.evaluation import EvaluationError
from independent_judge.domain.evidence import locate
from independent_judge.domain.judge_parsing import strict_json
from independent_judge.domain.paired_rubric import RUBRIC
from independent_judge.domain.run_manifest import digest


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Evidence(StrictModel):
    source_quote: str = Field(min_length=1, max_length=1800)
    translation_quote: str = Field(min_length=1, max_length=1800)
    kind: Literal['strength', 'defect', 'observation']
    explanation_en: str = Field(min_length=1, max_length=2000)
    explanation_ru: str = Field(min_length=1, max_length=2000)


class Assessment(StrictModel):
    status: Literal['assessed', 'not_assessed', 'not_applicable']
    score: int | None = Field(ge=1, le=5)
    coverage: Literal['whole_selected_range', 'partial']
    explanation_en: str = Field(min_length=1, max_length=2000)
    explanation_ru: str = Field(min_length=1, max_length=2000)
    evidence: list[Evidence] = Field(max_length=3)


class Criterion(StrictModel):
    criterion: Literal['accuracy', 'completeness', 'terminology', 'readability', 'seamlessness', 'apparatus']
    a: Assessment
    b: Assessment


class CriticalError(StrictModel):
    side: Literal['a', 'b']
    category: Literal['meaning_reversed', 'content_invented', 'unit_omitted', 'quotation_corrupted', 'attribution_wrong']
    source_quote: str = Field(min_length=1, max_length=1800)
    translation_quote: str = Field(min_length=1, max_length=1800)
    explanation_en: str = Field(min_length=1, max_length=2000)
    explanation_ru: str = Field(min_length=1, max_length=2000)


class Response(StrictModel):
    criteria: list[Criterion] = Field(min_length=1, max_length=6)
    critical_errors: list[CriticalError] = Field(max_length=40)


def _anchor(scope, side: str, item: dict) -> dict:
    anchors = {'source': locate(scope.texts['source'], item['source_quote']),
               'translation': locate(scope.texts[side], item['translation_quote'])}
    return item | {'anchors': anchors, 'verified': all(a['status'] == 'verified' for a in anchors.values()),
                   'id': digest([side, item['source_quote'], item['translation_quote']])[:24]}


def parse_assessment(text: str, scope, order=('a', 'b'), *, expected=None) -> dict:
    if len(order) != 2 or set(order) != {'a', 'b'}:
        raise EvaluationError('invalid_order', 'Expected exactly two anonymous sides.')
    try:
        parsed = Response.model_validate(strict_json(text))
    except ValidationError as exc:
        raise EvaluationError('invalid_paired_response', 'Paired response does not match the complete schema.') from exc
    expected = set(RUBRIC) if expected is None else set(expected)
    if len(parsed.criteria) != len(expected) or {r.criterion for r in parsed.criteria} != expected:
        raise EvaluationError('invalid_paired_response', 'Each criterion must occur exactly once.')
    rows = []
    for row in parsed.criteria:
        out = {'criterion': row.criterion}
        for label, side in zip(('a', 'b'), order):
            assessment = getattr(row, label).model_dump()
            if (assessment['status'] == 'assessed') != (assessment['score'] is not None):
                raise EvaluationError('invalid_paired_response', 'Only assessed criteria may have a score.')
            assessment['evidence'] = [_anchor(scope, side, e) for e in assessment['evidence']]
            out[side] = assessment
        rows.append(out)
    sides = dict(zip(('a', 'b'), order))
    critical = [_anchor(scope, sides[e.side], e.model_dump() | {'side': sides[e.side]}) for e in parsed.critical_errors]
    return {'criteria': rows, 'critical_errors': critical, 'order': list(order)}
