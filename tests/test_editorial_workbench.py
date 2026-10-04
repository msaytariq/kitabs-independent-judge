"""Measured work has immutable provenance; uncertainty must never become zero."""
from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from independent_judge.api.app import create_app
from test_scope import draft, selection


def review(tmp_path):
    app = create_app(tmp_path)
    c = TestClient(app)
    d = draft(c)
    scope = c.post(f"/api/comparisons/{d['id']}/scopes", json=selection(d)).json()
    r = c.post('/api/editorial', json={'scope_id':scope['id'], 'rubric':'Meaning, terminology, citations and readability', 'actor':'editor-1'})
    assert r.status_code == 201, r.text
    state = r.json()
    clock = [state['created_at_ms']]
    app.state.editorial.clock = lambda: clock[0]
    return c, state, clock


def request(state, kind, **params):
    return {'expected_revision':state['revision'], 'command_id':uuid4().hex,
            'actor':'editor-1', 'kind':kind, 'params':params}


def act(c, state, kind, **params):
    r = c.post(f"/api/editorial/{state['id']}/commands", json=request(state,kind,**params))
    assert r.status_code == 200, r.text
    return r.json()


def head(state, side='a'):
    return state['sides'][side]['versions'][-1]


def finish_side(c, state, clock, side, milliseconds=1000):
    state=act(c,state,'start',side=side,stage='verification')
    clock[0]+=milliseconds
    state=act(c,state,'stop')
    return act(c,state,'accept',side=side,expected_sha256=head(state,side)['sha256'],confirmed=True,
               reason='Reviewed against the common publication rubric.')


def test_review_preserves_scope_rubric_and_survives_restart(tmp_path):
    c,s,clock=review(tmp_path)
    assert s['metrics']['savings_percent'] is None
    assert s['metrics']['sides']['a']['total_seconds'] is None
    assert s['sides']['a']['prior_work']['status']=='unknown'
    assert head(s)['text']=='Intro.\n\nSame passage.\n\nSame passage.'
    with TestClient(create_app(tmp_path)) as second:
        assert second.get(f"/api/editorial/{s['id']}").json()==s


def test_pause_excluded_and_prior_work_included_in_savings(tmp_path):
    c,s,t=review(tmp_path)
    s=act(c,s,'prior_work',side='a',status='reported',seconds=120,reason='Editor log A, externally recorded')
    s=act(c,s,'prior_work',side='b',status='reported',seconds=60,reason='Kitabs expert log, externally recorded')
    s=act(c,s,'start',side='a',stage='editing')
    t[0]+=30000; s=act(c,s,'pause')
    t[0]+=900000; s=act(c,s,'resume')
    t[0]+=30000; s=act(c,s,'stop')
    s=finish_side(c,s,t,'a',10000)
    s=finish_side(c,s,t,'b',10000)
    assert s['metrics']['sides']['a']['editing_seconds']==60
    assert s['metrics']['sides']['a']['total_seconds']==190
    assert s['metrics']['sides']['b']['total_seconds']==70
    assert s['metrics']['savings_percent']==pytest.approx(63.1578947368)
    assert s['metrics']['measurement']=='operator_timed_plus_declared_prior_work'


def test_unknown_prior_work_blocks_claim_even_after_acceptance(tmp_path):
    c,s,t=review(tmp_path)
    s=finish_side(c,s,t,'a');s=finish_side(c,s,t,'b')
    assert s['metrics']['savings_percent'] is None
    assert 'unknown_prior_work' in s['metrics']['unavailable_reasons']


def test_negative_savings_retained(tmp_path):
    c,s,t=review(tmp_path)
    for side in ['a','b']:
        s=act(c,s,'prior_work',side=side,status='none',seconds=0,reason='No prior human editing; recorded at input.')
    s=finish_side(c,s,t,'a',1000);s=finish_side(c,s,t,'b',2000)
    assert s['metrics']['savings_percent']==-100


def test_versions_and_task_decisions_invalidate_on_later_edit(tmp_path):
    c,s,t=review(tmp_path); initial=head(s)
    s=act(c,s,'add_task',side='a',category='meaning',title='Check opening',
          start=0,end=5,expected_sha256=initial['sha256'])
    task=s['sides']['a']['tasks'][0]['id']
    s=act(c,s,'decide_task',side='a',task_id=task,status='dismissed',reason='Confirmed against source',expected_sha256=initial['sha256'])
    s=finish_side(c,s,t,'a')
    assert s['sides']['a']['acceptance'] is not None
    s=act(c,s,'start',side='a',stage='editing')
    s=act(c,s,'save_version',side='a',text='Revised opening.\n\nSame passage.',
          expected_sha256=initial['sha256'],reason='Editorial correction')
    assert s['sides']['a']['versions'][0]==initial
    assert len(s['sides']['a']['versions'])==2
    assert s['sides']['a']['acceptance'] is None
    assert s['metrics']['sides']['a']['pending_tasks']==1
    assert s['metrics']['sides']['a']['stale_decisions']==1


def test_acceptance_requires_stopped_verification_and_resolved_tasks(tmp_path):
    c,s,t=review(tmp_path)
    args={'side':'a','expected_sha256':head(s)['sha256'],'confirmed':True,'reason':'Reviewed'}
    assert c.post(f"/api/editorial/{s['id']}/commands",json=request(s,'accept',**args)).status_code==422
    s=act(c,s,'add_task',side='a',category='hadith',title='Verify reference',start=0,end=5,expected_sha256=head(s)['sha256'])
    s=act(c,s,'start',side='a',stage='verification');t[0]+=1000;s=act(c,s,'stop')
    assert c.post(f"/api/editorial/{s['id']}/commands",json=request(s,'accept',**args)).status_code==422
    s=act(c,s,'decide_task',side='a',task_id=s['sides']['a']['tasks'][0]['id'],status='resolved',reason='Source verified',expected_sha256=head(s)['sha256'])
    s=act(c,s,'accept',**args)
    assert s['sides']['a']['acceptance']['rubric_sha256']==s['rubric']['sha256']


def test_duplicate_command_is_idempotent_and_changed_payload_rejected(tmp_path):
    c,s,t=review(tmp_path);req=request(s,'start',side='a',stage='editing')
    url=f"/api/editorial/{s['id']}/commands"
    first=c.post(url,json=req); assert first.status_code==200
    t[0]+=5000
    assert c.post(url,json=req).json()==first.json()
    assert c.post(url,json=req|{'params':{'side':'b','stage':'editing'}}).status_code==409
    assert len(first.json()['sessions'])==1


def test_malformed_retry_returns_validation_error_without_changing_history(tmp_path):
    import json
    c,s,t=review(tmp_path)
    body=request(s,'start',side='a',stage='editing')
    url=f"/api/editorial/{s['id']}/commands"
    saved=c.post(url,json=body).json()
    body['params']['stage']=float('nan')
    response=c.post(url,content=json.dumps(body),headers={'Content-Type':'application/json'})
    assert response.status_code==422
    assert c.get(f"/api/editorial/{s['id']}").json()==saved


def test_stale_revision_or_text_cannot_overwrite_work(tmp_path):
    c,s,t=review(tmp_path);old=s
    s=act(c,s,'start',side='a',stage='editing')
    url=f"/api/editorial/{s['id']}/commands"
    assert c.post(url,json=request(old,'pause')).status_code==409
    assert c.post(url,json=request(s,'save_version',side='a',text='changed',expected_sha256='0'*64,reason='edit')).status_code==422
    assert c.get(f"/api/editorial/{s['id']}").json()==s


def test_editor_cannot_run_overlapping_sessions_across_reviews(tmp_path):
    c,a,t=review(tmp_path)
    b=c.post('/api/editorial',json={'scope_id':a['scope_id'],'rubric':a['rubric']['text'],'actor':'editor-1'}).json()
    a=act(c,a,'start',side='a',stage='editing')
    r=c.post(f"/api/editorial/{b['id']}/commands",json=request(b,'start',side='b',stage='editing'))
    assert r.status_code==409
    a=act(c,a,'pause')
    b=act(c,b,'start',side='b',stage='editing')
    assert c.post(f"/api/editorial/{a['id']}/commands",json=request(a,'resume')).status_code==409


@pytest.mark.parametrize('status,seconds',[('reported',-1),('reported',True),('reported',None),('reported',10**400),('none',5),('unknown',0)])
def test_invalid_prior_time_rejected(tmp_path,status,seconds):
    c,s,t=review(tmp_path)
    r=c.post(f"/api/editorial/{s['id']}/commands",json=request(s,'prior_work',side='a',status=status,seconds=seconds,reason='Prior record'))
    assert r.status_code==422


def test_nonfinite_json_numbers_cannot_reach_event_storage(tmp_path):
    import json
    c,s,t=review(tmp_path)
    body=request(s,'prior_work',side='a',status='reported',seconds=float('nan'),reason='Invalid number')
    response=c.post(f"/api/editorial/{s['id']}/commands",content=json.dumps(body),headers={'Content-Type':'application/json'})
    assert response.status_code==422
    assert c.get(f"/api/editorial/{s['id']}").json()==s


def test_edit_needs_active_matching_session_and_fresh_final_verification(tmp_path):
    c,s,t=review(tmp_path)
    params={'side':'a','text':'Revised text','expected_sha256':head(s)['sha256'],'reason':'Correction'}
    url=f"/api/editorial/{s['id']}/commands"
    assert c.post(url,json=request(s,'save_version',**params)).status_code==422
    s=finish_side(c,s,t,'a')
    s=act(c,s,'start',side='a',stage='editing')
    s=act(c,s,'save_version',**params)
    s=act(c,s,'stop')
    assert c.post(url,json=request(s,'accept',side='a',expected_sha256=head(s)['sha256'],confirmed=True,reason='Reuse old verification')).status_code==422


def test_clock_rollback_rejected(tmp_path):
    c,s,t=review(tmp_path);s=act(c,s,'start',side='a',stage='editing');t[0]-=1
    assert c.post(f"/api/editorial/{s['id']}/commands",json=request(s,'stop')).status_code==422


def test_export_keeps_event_history_and_labels_source_of_time(tmp_path):
    c,s,t=review(tmp_path)
    s=act(c,s,'prior_work',side='a',status='none',seconds=0,reason='No prior editor')
    r=c.get(f"/api/editorial/{s['id']}/export")
    assert r.status_code==200
    export=r.json()
    assert export['state']==s
    assert len(export['events'])==2
    assert export['events'][1]['command']['kind']=='prior_work'
    assert 'attention' in ' '.join(export['limitations'])
    assert 'attachment' in r.headers['content-disposition']


def test_public_hosts_and_cross_origin_mutations_blocked(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        assert c.get('/health',headers={'Host':'evil.example'}).status_code==403
        assert c.post('/api/editorial',json={},headers={'Origin':'https://evil.example'}).status_code==403
        assert c.post('/api/editorial',json={},headers={'Origin':'null'}).status_code==403
