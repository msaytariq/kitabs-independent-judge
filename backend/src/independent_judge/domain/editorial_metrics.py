"""Deterministic evidence summaries. Unknown time is never replaced with zero."""
from independent_judge.domain.editorial_sessions import closed_milliseconds


def task_status(task, version):
    if task['decision'] is None:
        return 'open'
    if task['decision']['version']!=version:
        return 'needs_recheck'
    return task['decision']['status']


def metrics(state):
    sides={}
    reasons=[]
    for role,document in state['sides'].items():
        version=document['versions'][-1]['number']
        statuses=[task_status(t,version) for t in document['tasks']]
        durations={stage:sum(closed_milliseconds(s) for s in state['sessions']
                    if s['side']==role and s['stage']==stage)/1000 for stage in ('editing','verification')}
        tracked=sum(durations.values())
        prior=document['prior_work']
        total=None if prior['status']=='unknown' else tracked+prior['seconds']
        sides[role]={'editing_seconds':durations['editing'],'verification_seconds':durations['verification'],
            'tracked_seconds':tracked,'prior_seconds':prior['seconds'],'prior_status':prior['status'],
            'total_seconds':total,'pending_tasks':sum(v not in ('resolved','dismissed') for v in statuses),
            'dismissed_tasks':statuses.count('dismissed'),'stale_decisions':statuses.count('needs_recheck'),
            'accepted':document['acceptance'] is not None}
        if prior['status']=='unknown': reasons.append('unknown_prior_work')
        if document['acceptance'] is None: reasons.append('publication_standard_not_accepted')
        if sides[role]['pending_tasks']: reasons.append('pending_tasks')
    if any(s['status']!='stopped' for s in state['sessions']): reasons.append('unfinished_session')
    if sides['a']['total_seconds']==0: reasons.append('zero_baseline_time')
    saving=None
    if not reasons:
        a,b=sides['a']['total_seconds'],sides['b']['total_seconds']
        saving=(a-b)/a*100
    return {'measurement':'operator_timed_plus_declared_prior_work','sides':sides,
            'savings_percent':saving,'unavailable_reasons':sorted(set(reasons))}
