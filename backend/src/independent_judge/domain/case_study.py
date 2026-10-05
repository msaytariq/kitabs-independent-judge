"""What the judge caught in each translation and what Kitabs corrected on its way to B."""
from independent_judge.domain.paired_rubric import RUBRIC

MAX_DEFECTS = 3
MAX_CORRECTIONS = 2
MAX_CORRECTION_CHARS = 200
_FIELDS = ('source_quote', 'translation_quote', 'explanation_en', 'explanation_ru')


def _defects(rubric: dict, side: str) -> list[dict]:
    indexed = {row['criterion']: row for row in rubric['criteria']}
    found, seen = [], set()
    for criterion in RUBRIC:  # Accuracy first: the rubric order is the order of importance.
        for item in (indexed.get(criterion) or {}).get(side, {}).get('evidence', []):
            if item.get('kind') != 'defect' or item.get('verified') is not True or item['id'] in seen:
                continue
            seen.add(item['id'])
            found.append({'id': item['id'], 'criterion': criterion} | {k: item.get(k, '') for k in _FIELDS})
    return found[:MAX_DEFECTS]


def _corrections(processing: dict | None) -> list[dict]:
    operations = (((processing or {}).get('sides') or {}).get('b') or {}).get('operations') or []
    short = [op for op in operations if op['stage'] == 'audit'
             and max(len(op['before']), len(op['after'])) <= MAX_CORRECTION_CHARS]
    return [{'stage': op['stage'], 'before': op['before'], 'after': op['after']} for op in short[:MAX_CORRECTIONS]]


def case_study(rubric: dict | None, processing: dict | None) -> dict | None:
    if not rubric:
        return None
    return {'a': _defects(rubric, 'a'), 'b': _defects(rubric, 'b'), 'kitabs_corrections': _corrections(processing)}
