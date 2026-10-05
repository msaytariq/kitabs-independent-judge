"""Free observable signals. Heuristics neither repair text nor assign grades."""
import re
from independent_judge.domain.apparatus_inventory import inventory


def structural_checks(texts: dict, boundaries=None) -> dict:
    results = {}
    for side in ('a', 'b'):
        text, signals = texts[side], []
        seen = set()
        for paragraph in re.split(r'\n\s*\n', text):
            paragraph = paragraph.strip()
            if paragraph and paragraph in seen:
                signals.append({'kind': 'repeated_paragraph', 'confidence': 'heuristic', 'quote': paragraph,
                                'present_in_source': paragraph in texts['source']})
            seen.add(paragraph)
        definitions = set(re.findall(r'^\s*\[(\^?\d+|(?:fn|en):\d+)\]\s*:', text, re.M))
        markers = set(re.findall(r'\[(\^?\d+|(?:fn|en):\d+)\]', text))
        for marker in sorted(markers - definitions):
            signals.append({'kind': 'unresolved_note_marker', 'confidence': 'heuristic', 'quote': '[' + marker + ']',
                            'present_in_source': '[' + marker + ']' in texts['source']})
        # Metadata is evidence of known boundaries only, not proof of correct seams.
        known = (boundaries or {}).get(side)
        results[side] = {'signals': signals, 'inventory': inventory(text),
                         'chunk_boundary_coverage': 'supplied' if known else 'unknown',
                         'boundaries': known or [], 'scope': 'observable_text_only'}
    return results
