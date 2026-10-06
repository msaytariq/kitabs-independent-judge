"""Verbatim quote anchors; repeated matches remain ambiguous, never guessed."""

# Invisible direction marks; a quote never needs them to be found.
_MARKS = frozenset('\u200e\u200f\u061c\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069')


def _compact(text: str) -> tuple[str, list[int]]:
    """The text without direction marks and with each run of spaces as one space, and the original
    position of each kept character. A line break in the text does not break a quote."""
    kept, positions = [], []
    for index, char in enumerate(text):
        if char in _MARKS:
            continue
        if char.isspace():
            if not kept or kept[-1] == ' ':
                continue
            char = ' '
        kept.append(char)
        positions.append(index)
    return ''.join(kept), positions


def locate(text: str, quote: str) -> dict:
    needle = _compact(quote)[0].strip()
    if not needle:
        return {'status':'missing','ranges':[]}
    haystack, positions = _compact(text)
    starts=[]; position=0
    while (position := haystack.find(needle, position)) != -1:
        starts.append({'start':positions[position],'end':positions[position+len(needle)-1]+1})
        position += 1
    return {'status': 'verified' if len(starts)==1 else 'ambiguous' if starts else 'missing',
            'ranges':starts}


def anchor_finding(finding: dict, source: str, translation: str) -> dict:
    anchors={'source':locate(source,finding['source_excerpt']),
             'translation':locate(translation,finding['current_text'])}
    statuses={v['status'] for v in anchors.values()}
    status='missing' if 'missing' in statuses else 'ambiguous' if 'ambiguous' in statuses else 'verified'
    return {**finding,'evidence_status':status,'anchors':anchors}
