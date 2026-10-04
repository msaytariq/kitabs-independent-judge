"""Verbatim quote anchors; repeated matches remain ambiguous, never guessed."""

def locate(text: str, quote: str) -> dict:
    if not quote or not quote.strip():
        return {'status':'missing','ranges':[]}
    starts=[]; position=0
    while (position := text.find(quote, position)) != -1:
        starts.append({'start':position,'end':position+len(quote)})
        position += 1
    return {'status': 'verified' if len(starts)==1 else 'ambiguous' if starts else 'missing',
            'ranges':starts}


def anchor_finding(finding: dict, source: str, translation: str) -> dict:
    anchors={'source':locate(source,finding['source_excerpt']),
             'translation':locate(translation,finding['current_text'])}
    statuses={v['status'] for v in anchors.values()}
    status='missing' if 'missing' in statuses else 'ambiguous' if 'ambiguous' in statuses else 'verified'
    return {**finding,'evidence_status':status,'anchors':anchors}
