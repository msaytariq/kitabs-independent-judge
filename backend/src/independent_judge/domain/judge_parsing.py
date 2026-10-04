"""Strict JSON contracts; bad responses never become successful empty findings."""
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, StrictBool, Field, ValidationError
from independent_judge.domain.evaluation import EvaluationError
from independent_judge.domain.evidence import anchor_finding


class Finding(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    code: Literal['K','T','A','S']
    source_excerpt: str = Field(min_length=1, max_length=1800)
    current_text: str = Field(min_length=1, max_length=1800)
    should_be: str = Field(min_length=1, max_length=1800)
    why: str = Field(min_length=1, max_length=2500)
    repeated: StrictBool = False


class Findings(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    findings: list[Finding] = Field(max_length=25)


def strict_json(text: str) -> dict:
    # Markdown fences are an envelope, not a license to repair partial JSON.
    text=text.strip()
    if text.startswith('```json\n') and text.endswith('\n```'):
        text=text[8:-4]
    def unique(pairs):
        out={}
        for key,value in pairs:
            if key in out: raise ValueError('duplicate field')
            out[key]=value
        return out
    try:
        obj=json.loads(text, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if not isinstance(obj,dict): raise ValueError()
        return obj
    except (ValueError,TypeError) as exc:
        raise EvaluationError('invalid_json','Judge returned invalid JSON.') from exc


def parse_findings(text: str, source: str, translation: str) -> list[dict]:
    try:
        parsed=Findings.model_validate(strict_json(text))
    except ValidationError as exc:
        raise EvaluationError('invalid_findings','Judge findings do not match the schema.') from exc
    return [anchor_finding(f.model_dump(),source,translation) for f in parsed.findings]
