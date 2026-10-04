"""Symmetric cross-check candidates remain separate from majority-confirmed counts."""
from independent_judge.domain.cross_check_prompt import cross_prompt
from independent_judge.domain.review_parsing import decisions,CrossDecision
from independent_judge.domain.evidence import anchor_finding


def cross_check(scope,side,other_findings,call):
    if not other_findings: return []
    reviews=decisions(call('cross-'+side,cross_prompt(scope,side,other_findings)),len(other_findings),CrossDecision)
    for r in reviews:
        if r['finding'] is not None:
            r['finding']=anchor_finding(r['finding'],scope.texts['source'],scope.texts[side])
            r['finding']['status']='single_review_candidate'
    return reviews
