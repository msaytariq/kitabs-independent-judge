"""Conservative two-of-three consensus over exact evidence locations."""
from collections import Counter


def consensus(passes: list[list[dict]]) -> list[dict]:
    clusters={}
    for pass_index,findings in enumerate(passes):
        for f in findings:
            if f['evidence_status'] != 'verified': continue
            # Keep different locations distinct. No fuzzy match or chained substring merging.
            key=(f['source_excerpt'], f['current_text'])
            clusters.setdefault(key,{})[pass_index]=f
    result=[]
    for votes in clusters.values():
        if len(votes)<2: continue
        counts=Counter(f['code'] for f in votes.values())
        # Ties do not escalate severity; retain the less severe interpretation.
        code=max(counts, key=lambda c:(counts[c], 'KTAS'.index(c)))
        chosen=next(f for f in votes.values() if f['code']==code)
        result.append({**chosen,'votes':len(votes),'consensus':'exact-quotes-2-of-3-v1'})
    return result
