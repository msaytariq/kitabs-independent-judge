import importlib
from threading import Event
import time
import pytest
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash
from independent_judge.application.intake import Upload


class Platform:
    def __init__(self): self.starts = 0; self.creates = 0; self.done = False
    def ready(self): return True
    def upload(self, source, source_language, target_language): return 'doc'
    def create(self, document_id): self.creates += 1; return 'job'
    def start(self, job_id): self.starts += 1; self.done = True
    def status(self, job_id): return {'id': job_id, 'status': 'completed' if self.done else 'running'}
    def completed(self, job_id, source_sha256, started_at=None):
        self.started_at = started_at
        return {'job_id': job_id, 'text': 'Translation B', 'sha256': text_hash('Translation B'),
                'source_sha256': source_sha256, 'state': 'completed', 'processing': None}


def service(tmp_path, port):
    from independent_judge.infrastructure.text_extractors import LocalTextExtractor
    cls = importlib.import_module('independent_judge.application.pipeline_b').PipelineBService
    repo = importlib.import_module('independent_judge.infrastructure.pipeline_jobs').PipelineJobs(tmp_path)
    return cls(repo, port, LocalTextExtractor())


def submit(s, request_id='r', source='الأصل'):
    return s.submit(request_id, Upload(source.encode(), 'source.txt', 'text/plain'), 'ar', 'en')


def wait(s, key='r'):
    for _ in range(100):
        out = s.status(key)
        if out['status'] in ('completed', 'failed') or (out['status'] == 'uncertain' and not out['job_id']): return out
        time.sleep(.01)
    raise AssertionError('Pipeline did not finish')


def test_repeated_launch_and_reload_keep_one_paid_job(tmp_path):
    port = Platform()
    s = service(tmp_path, port)
    try:
        submit(s); submit(s)
        out = wait(s)
        assert out['status'] == 'completed'
        assert out['result']['text'] == 'Translation B'
        assert port.starts == port.creates == 1
    finally: s.close()
    restored = service(tmp_path, port)
    try:
        assert restored.status('r')['job_id'] == 'job'
        submit(restored)
        assert port.starts == 1
    finally: restored.close()


def test_same_id_with_different_original_cannot_launch_again(tmp_path):
    s = service(tmp_path, Platform())
    try:
        submit(s)
        with pytest.raises(InputError): submit(s, source='different')
    finally: s.close()


def test_lost_start_response_recovers_with_read_only_status(tmp_path):
    class Lost(Platform):
        def start(self, job_id):
            super().start(job_id)
            raise InputError('pipeline_unavailable', 'lost response')
    port = Lost(); s = service(tmp_path, port)
    try:
        submit(s)
        assert wait(s)['status'] == 'completed'
        assert port.starts == 1
    finally: s.close()


def test_lost_create_response_does_not_create_replacement(tmp_path):
    class Lost(Platform):
        def create(self, doc):
            self.creates += 1
            raise InputError('pipeline_unavailable', 'lost response')
    port = Lost(); s = service(tmp_path, port)
    try:
        submit(s)
        assert wait(s)['status'] == 'uncertain'
        submit(s)
        assert port.creates == 1 and port.starts == 0
    finally: s.close()


def test_source_limits_and_disabled_adapter_fail_before_work(tmp_path):
    s = service(tmp_path, None)
    try:
        with pytest.raises(InputError): submit(s)
    finally: s.close()


def test_http_pipeline_result_is_bound_to_saved_scope(tmp_path):
    from fastapi.testclient import TestClient
    from independent_judge.api.app import create_app
    s = service(tmp_path, Platform())
    with TestClient(create_app(tmp_path, pipeline=s)) as client:
        response = client.post('/api/pipeline-b', data={'request_id': 'http', 'source_kind': 'text',
            'source_value': 'الأصل', 'source_language': 'ar', 'target_language': 'en'})
        assert response.status_code == 202
        done = wait(s, 'http')
        draft = client.post('/api/comparisons/text', json={'source': 'الأصل', 'a': 'A',
            'b': done['result']['text'], 'source_language': 'ar', 'target_language': 'en'}).json()
        data = {'confirmed': True, 'profile': 'general', 'pipeline_request_id': 'http', 'ranges': {
            k: {'start': 0, 'end': len(v['text']), 'text_sha256': v['sha256']} for k,v in draft['materials'].items()}}
        scope = client.post(f"/api/comparisons/{draft['id']}/scopes", json=data)
        assert scope.status_code == 201
        assert scope.json()['pipeline']['job_id'] == 'job'
        assert scope.json()['processing']['b'] is None
    port = Platform(); s = service(tmp_path, port)
    try:
        with pytest.raises(InputError): submit(s, source='x' * 18001)
        assert port.creates == port.starts == 0
    finally: s.close()


def test_launch_limit_stops_new_paid_jobs_but_keeps_existing_requests(tmp_path):
    from independent_judge.infrastructure.text_extractors import LocalTextExtractor
    from independent_judge.application.pipeline_b import PipelineBService
    from independent_judge.infrastructure.pipeline_jobs import PipelineJobs
    port = Platform()
    s = PipelineBService(PipelineJobs(tmp_path), port, LocalTextExtractor(), max_requests=2)
    try:
        assert s.remaining() == 2
        submit(s, 'one'); wait(s, 'one')
        submit(s, 'two', 'نص آخر'); wait(s, 'two')
        assert s.remaining() == 0
        with pytest.raises(InputError) as refused:
            submit(s, 'three', 'نص ثالث')
        assert refused.value.code == 'pipeline_limit_reached'
        assert submit(s, 'one')['status'] == 'completed'  # A known request is read, never launched again.
        assert port.starts == 2
    finally: s.close()
    assert PipelineBService(PipelineJobs(tmp_path), None, LocalTextExtractor()).remaining() is None


def test_capabilities_report_the_remaining_launches(tmp_path):
    from fastapi.testclient import TestClient
    from independent_judge.api.pipeline_b import build_pipeline_router
    from fastapi import FastAPI
    from independent_judge.infrastructure.text_extractors import LocalTextExtractor
    from independent_judge.application.pipeline_b import PipelineBService
    from independent_judge.infrastructure.pipeline_jobs import PipelineJobs
    app = FastAPI()
    app.include_router(build_pipeline_router(PipelineBService(PipelineJobs(tmp_path), Platform(), LocalTextExtractor(), max_requests=10), None))
    assert TestClient(app).get('/api/pipeline-b/capabilities').json() == {'enabled': True, 'remaining': 10}


def test_capabilities_are_off_while_no_operator_account_is_connected(tmp_path):
    from fastapi.testclient import TestClient
    from independent_judge.api.pipeline_b import build_pipeline_router
    from fastapi import FastAPI
    from independent_judge.infrastructure.text_extractors import LocalTextExtractor
    from independent_judge.application.pipeline_b import PipelineBService
    from independent_judge.infrastructure.pipeline_jobs import PipelineJobs
    port = Platform()
    port.ready = lambda: False
    app = FastAPI()
    app.include_router(build_pipeline_router(PipelineBService(PipelineJobs(tmp_path), port, LocalTextExtractor(), max_requests=10), None))
    assert TestClient(app).get('/api/pipeline-b/capabilities').json() == {'enabled': False, 'remaining': 10}


def test_the_start_moment_is_saved_before_the_paid_start_and_reaches_the_journal(tmp_path):
    port = Platform()
    s = service(tmp_path, port)
    try:
        submit(s)
        out = wait(s)
        assert out['status'] == 'completed'
        assert isinstance(out['started_at'], float) and port.started_at == out['started_at']
    finally: s.close()


def test_no_launch_is_used_while_no_operator_account_is_connected(tmp_path):
    port = Platform()
    port.ready = lambda: False
    s = service(tmp_path, port)
    s.max_requests = 2
    try:
        with pytest.raises(InputError) as refused:
            submit(s, 'one')
        assert refused.value.code == 'pipeline_auth_required'
        assert s.remaining() == 2 and port.creates == 0
    finally: s.close()
