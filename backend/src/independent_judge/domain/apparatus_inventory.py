"""English structural inventory v1. Presence is not relevance or correctness."""
import re

NOTE = re.compile(r'^\s*\[\^?(\d+)\]\s*:?\s+\S', re.M)
ENTRY = re.compile(r'^\s*(?:[-*•]|\d+[.)])\s+\S')
GLOSSARY = re.compile(r'^\s*(?:[-*•]\s+)?[^:\n—]{1,80}\s*[:—]\s*\S')
HEADINGS = {'notes': 'notes', 'footnotes': 'notes', 'endnotes': 'notes',
            'general notes': 'notes', 'glossary': 'glossary',
            'persons': 'persons', 'narrators': 'persons', 'narrator notes': 'persons',
            'report notes': 'persons', 'biographical notes': 'persons'}


def inventory(text: str) -> dict:
    result = {'notes': len(set(NOTE.findall(text))), 'glossary': 0, 'persons': 0}
    section = None
    for line in text.splitlines():
        heading = line.strip().strip('#* ').rstrip(':').lower()
        if heading in HEADINGS:
            section = HEADINGS[heading]
        elif line.lstrip().startswith('#'):
            section = None
        elif section and (GLOSSARY if section == 'glossary' else ENTRY).match(line):
            result[section] += 1
    return result


def structural_score(items: dict, *, source_notes: int) -> float:
    share = min(1, items['notes'] / source_notes) if source_notes else bool(items['notes'])
    # Same 5/3/2 structural allocation as the platform, on a 0–100 scale.
    return round(5 * share + 3 * bool(items['glossary']) + 2 * bool(items['persons']), 1) * 10
