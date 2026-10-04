"""Exact user-selected ranges in Unicode code points, without text rewriting."""
from dataclasses import dataclass, asdict
from hashlib import sha256
from independent_judge.domain.errors import InputError
from independent_judge.domain.inputs import InputTriple
from independent_judge.domain.profiles import profile_policy


def text_hash(text: str) -> str:
    return sha256(text.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class TextRange:
    start: int
    end: int
    text_sha256: str  # Hash of the entire extracted input, not just the selected slice.


@dataclass(frozen=True)
class PreparedComparison:
    texts: dict[str, str]
    hashes: dict[str, str]
    ranges: dict[str, dict]
    profile: str
    source_language: str
    target_language: str
    status: str
    sampling_version: str = 'manual-codepoints-v1'


def prepare_scope(inputs: InputTriple, source_range: TextRange, a_range: TextRange,
                  b_range: TextRange, source_lang: str, target_lang: str,
                  profile: str, *, confirmed: bool = False) -> PreparedComparison:
    profile_policy(profile)
    if (source_lang, target_lang) != (inputs.source_language, inputs.target_language):
        raise InputError('language_mismatch', 'Languages must match the stored inputs.')
    texts, ranges = {}, {}
    for material, selection in zip(inputs.materials, (source_range, a_range, b_range)):
        if selection.text_sha256 != material.sha256 or text_hash(material.text) != material.sha256:
            raise InputError('stale_input', 'Input changed; select and confirm the ranges again.')
        if (type(selection.start) is not int or type(selection.end) is not int
                or not 0 <= selection.start < selection.end <= len(material.text)):
            raise InputError('invalid_range', 'Use nonempty half-open Unicode code-point ranges.')
        text = material.text[selection.start:selection.end]
        if not text.strip():
            raise InputError('empty_range', 'A selected range has no readable text.')
        texts[material.role] = text
        ranges[material.role] = asdict(selection)
    if len(texts['source']) > 18000:
        raise InputError('scope_too_large', 'Select at most 18000 source characters; boundaries are never moved automatically.')
    return PreparedComparison(texts, {k: text_hash(v) for k, v in texts.items()}, ranges,
                              profile, source_lang, target_lang, 'ready' if confirmed else 'needs_review')
