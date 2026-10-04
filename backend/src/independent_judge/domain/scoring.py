"""Separate defect categories; no unsupported overall score or declared winner."""

def counts(findings):
    return {code:sum(f['code']==code for f in findings) for code in 'KTAS'}


def pending_review(passes,cross,coverage):
    return (any(f['evidence_status']!='verified' for side in passes.values() for p in side for f in p)
            or any(r['verdict']!='absent' for side in cross.values() for r in side)
            or any(coverage[s]['counts'][state] for s in ('a','b') for state in ('uncertain','needs_review')))
