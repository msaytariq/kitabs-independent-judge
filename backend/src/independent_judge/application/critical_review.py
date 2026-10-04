"""Apply critical appeals without altering original passes or evidence."""
from independent_judge.domain.critical_review_prompt import critical_prompt
from independent_judge.domain.review_parsing import decisions,CriticalDecision


def review_critical(scope,side,findings,call):
    candidates=[f for f in findings if f['code']=='K']
    if not candidates: return findings,[]
    reviews=decisions(call('critical-'+side,critical_prompt(scope,side,candidates)),len(candidates),CriticalDecision)
    result=[f for f in findings if f['code']!='K']
    for f,review in zip(candidates,reviews):
        if review['verdict']!='reject': result.append({**f,'code':review['code'],'critical_review':review})
    return result,reviews
