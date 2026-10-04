"""Complete decision sets: missing or duplicate reviews are never implicit acquittals."""
from typing import Literal
from pydantic import BaseModel,ConfigDict,StrictInt,Field,ValidationError
from independent_judge.domain.judge_parsing import Finding, strict_json
from independent_judge.domain.evaluation import EvaluationError


class CriticalDecision(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    index: StrictInt
    verdict: Literal['keep','reject','downgrade']
    code: Literal['K','T','A','S']
    why: str=Field(min_length=1)


class CrossDecision(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    index: StrictInt
    verdict: Literal['present','absent','uncertain']
    finding: Finding | None
    why: str=Field(min_length=1)


def decisions(text, count, schema):
    data=strict_json(text)
    if set(data)!={'decisions'} or not isinstance(data['decisions'],list):
        raise EvaluationError('invalid_review','Invalid review envelope.')
    try: rows=[schema.model_validate(x).model_dump() for x in data['decisions']]
    except ValidationError as exc: raise EvaluationError('invalid_review','Invalid review decision.') from exc
    if len(rows)!=count or {x['index'] for x in rows}!=set(range(count)):
        raise EvaluationError('incomplete_review','Every candidate needs exactly one decision.')
    for x in rows:
        if schema is CriticalDecision and ((x['verdict']=='keep' and x['code']!='K') or (x['verdict']=='downgrade' and x['code']=='K')):
            raise EvaluationError('invalid_review','Verdict and severity disagree.')
        if schema is CrossDecision and ((x['verdict']=='present') != (x['finding'] is not None)):
            raise EvaluationError('invalid_review','Present verdict requires a finding; others must be null.')
    return sorted(rows,key=lambda x:x['index'])
