"""Operator-controlled intervals; no inferred attention or model-estimated time."""
from independent_judge.domain.editorial_validation import require, side


def active_session(state):
    return next((s for s in state['sessions'] if s['status']!='stopped'),None)


def closed_milliseconds(session):
    return sum(i['end_ms']-i['start_ms'] for i in session['intervals'] if i['end_ms'] is not None)


def change_session(state, kind, params, actor, at_ms, command_id):
    active=active_session(state)
    if kind=='start':
        require(active is None,'Stop the existing session first.')
        document=side(state,params.get('side'))
        require(params.get('stage') in ('editing','verification'),'Choose editing or verification.')
        state['sessions'].append({'id':command_id,'side':params['side'],'stage':params['stage'],
            'actor':actor,'version':document['versions'][-1]['number'],
            'status':'running','intervals':[{'start_ms':at_ms,'end_ms':None}]})
        return
    require(active is not None,'There is no active session.')
    require(active['actor']==actor,'Only the session editor can control its timer.')
    if kind=='resume':
        require(active['status']=='paused','Only a paused session can resume.')
        active['intervals'].append({'start_ms':at_ms,'end_ms':None})
        active['status']='running'
    else:
        require(kind=='stop' or active['status']=='running','Only a running session can pause.')
        if active['status']=='running':
            active['intervals'][-1]['end_ms']=at_ms
        active['status']='stopped' if kind=='stop' else 'paused'


def require_editing(state, role, actor):
    active=active_session(state)
    require(active is not None and active['status']=='running' and active['side']==role
            and active['actor']==actor and active['stage']=='editing',
            'Start an editing session for this version before saving text.')


def has_final_verification(state, role, version):
    return any(s['side']==role and s['version']==version and s['stage']=='verification'
               and s['status']=='stopped' and closed_milliseconds(s)>0 for s in state['sessions'])
