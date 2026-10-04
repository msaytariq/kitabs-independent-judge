"""Publication decisions, immutable text versions and editorial task state."""
from copy import deepcopy
from independent_judge.domain.scope import text_hash
from independent_judge.domain.editorial_validation import require, text, side, current, seconds
from independent_judge.domain.editorial_sessions import change_session, require_editing, active_session, has_final_verification
from independent_judge.domain.editorial_metrics import task_status, metrics

CATEGORIES=('meaning','terminology','quran','hadith','apparatus','readability')
FIELDS={
    'start':{'side','stage'}, 'pause':set(), 'resume':set(), 'stop':set(),
    'prior_work':{'side','status','seconds','reason'},
    'save_version':{'side','text','expected_sha256','reason'},
    'add_task':{'side','category','title','start','end','expected_sha256'},
    'decide_task':{'side','task_id','status','reason','expected_sha256'},
    'accept':{'side','expected_sha256','confirmed','reason'},
}


def new_review(scope, rubric, actor, ident, at_ms):
    require(scope['status']=='ready','Confirm corresponding source and translation ranges first.')
    require(all(text_hash(v)==scope['hashes'][r] for r,v in scope['texts'].items()),'Scope hash mismatch.')
    require(all(len(v)<=200000 for v in scope['texts'].values()),'Choose at most 200000 characters per translation.')
    rubric=text(rubric,'Publication rubric',8000);actor=text(actor,'Editor label',80)
    state={'id':ident,'revision':0,'created_at_ms':at_ms,'updated_at_ms':at_ms,'scope_id':scope['id'],
        'scope':deepcopy(scope),'rubric':{'version':'editorial-rubric-v1','text':rubric,'sha256':text_hash(rubric)},
        'sides':{},'sessions':[]}
    for role in ('a','b'):
        state['sides'][role]={'versions':[{'number':0,'text':scope['texts'][role],
            'sha256':scope['hashes'][role],'at_ms':at_ms,'actor':actor,'reason':'Original selected input'}],
            'prior_work':{'status':'unknown','seconds':None,'reason':'Not yet documented'},
            'tasks':[],'acceptance':None}
    state['metrics']=metrics(state)
    return state


def apply_command(previous, command, at_ms):
    state=deepcopy(previous)
    require(at_ms>=state['updated_at_ms'],'Server clock moved backwards; no time recorded.')
    actor=text(command['actor'],'Editor label',80)
    kind,params=command['kind'],command['params']
    require(kind in FIELDS,'Unknown editorial action.')
    require(set(params)==FIELDS[kind],'Missing or unexpected action fields.')
    if kind in ('start','pause','resume','stop'):
        change_session(state,kind,params,actor,at_ms,command['command_id'])
    else:
        document=side(state,params['side'])
        if kind=='prior_work':
            _prior_work(document,params,actor,at_ms)
        else:
            version=current(document,params['expected_sha256'])
            if kind=='save_version':
                require_editing(state,params['side'],actor)
                value=params['text']
                text(value,'Edited text',200000)
                require(value!=version['text'],'The text has not changed.')
                require(len(document['versions'])<500,'Version limit reached for this local review.')
                document['versions'].append({'number':version['number']+1,'text':value,'sha256':text_hash(value),
                    'at_ms':at_ms,'actor':actor,'reason':text(params['reason'],'Edit reason')})
                document['acceptance']=None
            elif kind=='add_task':
                _add_task(document,params,version,actor,at_ms,command['command_id'])
            elif kind=='decide_task':
                _decide_task(document,params,version,actor,at_ms)
            elif kind=='accept':
                require(params['confirmed'] is True,'Explicit expert acceptance is required.')
                require(active_session(state) is None,'Stop the timer before accepting the final text.')
                require(has_final_verification(state,params['side'],version['number']),
                        'Complete a timed final verification of this exact text version.')
                require(all(task_status(t,version['number']) in ('resolved','dismissed') for t in document['tasks']),
                        'Resolve or dismiss all tasks, including stale decisions.')
                document['acceptance']={'version':version['number'],'sha256':version['sha256'],
                    'rubric_sha256':state['rubric']['sha256'],'actor':actor,'at_ms':at_ms,
                    'reason':text(params['reason'],'Acceptance reason')}
    state.update(revision=state['revision']+1,updated_at_ms=at_ms)
    state['metrics']=metrics(state)
    return state


def _prior_work(document,params,actor,at_ms):
    status,value=params['status'],params['seconds']
    require(status in ('unknown','none','reported'),'Unknown prior-work status.')
    if status=='unknown': require(value is None,'Unknown time must be null, not zero.')
    else:
        seconds(value)
        require(status!='none' or value==0,'No-prior-work means exactly zero seconds.')
    document['prior_work']={'status':status,'seconds':value,'actor':actor,'at_ms':at_ms,
                            'reason':text(params['reason'],'Prior-work evidence')}


def _add_task(document,params,version,actor,at_ms,ident):
    require(params['category'] in CATEGORIES,'Choose a supported task category.')
    a,b=params['start'],params['end']
    require(type(a) is int and type(b) is int and 0<=a<b<=len(version['text']),
            'Task anchor must be a nonempty Unicode code-point range.')
    require(len(document['tasks'])<1000,'Task limit reached for this local review.')
    document['tasks'].append({'id':ident,'category':params['category'],'title':text(params['title'],'Task description'),
        'anchor':{'version':version['number'],'sha256':version['sha256'],'start':a,'end':b,'quote':version['text'][a:b]},
        'actor':actor,'at_ms':at_ms,'decision':None})
    document['acceptance']=None


def _decide_task(document,params,version,actor,at_ms):
    task=next((t for t in document['tasks'] if t['id']==params['task_id']),None)
    require(task is not None,'Task not found.')
    require(params['status'] in ('confirmed','resolved','dismissed'),'Unknown task decision.')
    task['decision']={'status':params['status'],'reason':text(params['reason'],'Decision explanation'),
                     'version':version['number'],'sha256':version['sha256'],'actor':actor,'at_ms':at_ms}
    document['acceptance']=None
