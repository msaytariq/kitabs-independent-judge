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


class PlatformSource(Platform):
    """Kitabs reads the original file itself and returns its own source text with B."""
    def upload(self, source, source_language, target_language, original=None):
        self.source, self.original = source, original
        return 'doc'

    def completed(self, job_id, source_sha256, started_at=None):
        assert source_sha256 is None  # the platform text is the source of this comparison
        return {'job_id': job_id, 'text': 'Translation B', 'sha256': text_hash('Translation B'),
                'source': 'الله أكبر', 'source_sha256': text_hash('الله أكبر'), 'state': 'completed',
                'processing': {'job_id': job_id, 'source_sha256': text_hash('الله أكبر'), 'operations': []}}


class OrderDamagedPdf:
    """A PDF text layer with the legacy Allah glyph: the judge's own reader refuses it."""
    def extract(self, content, filename, content_type, check_order=True):
        from independent_judge.domain.inputs import ExtractedText
        if check_order:
            raise InputError('pdf_arabic_order_damaged', 'wrong order')
        return ExtractedText('هللا أكبر' * int(content.decode()), (), page_count=2)


def pdf_service(tmp_path, port):
    cls = importlib.import_module('independent_judge.application.pipeline_b').PipelineBService
    repo = importlib.import_module('independent_judge.infrastructure.pipeline_jobs').PipelineJobs(tmp_path)
    return cls(repo, port, OrderDamagedPdf())


def test_a_pdf_source_goes_to_kitabs_as_a_file_and_kitabs_text_becomes_the_source(tmp_path):
    port = PlatformSource()
    s = pdf_service(tmp_path, port)
    try:
        out = s.submit('pdf', Upload(b'1', 'book.pdf', 'application/pdf'), 'ar', 'en')
        assert out['source'] is None and out['source_sha256'] is None
        done = wait(s, 'pdf')
        assert port.source is None
        assert port.original == {'filename': 'book.pdf', 'content_type': 'application/pdf', 'content': b'1'}
        assert done['status'] == 'completed'
        assert done['source'] == 'الله أكبر' and done['source_sha256'] == text_hash('الله أكبر')
    finally: s.close()


def test_the_source_limits_apply_to_a_pdf_before_any_paid_work(tmp_path):
    port = PlatformSource()
    s = pdf_service(tmp_path, port)
    try:
        with pytest.raises(InputError) as caught:
            s.submit('big', Upload(b'3000', 'book.pdf', 'application/pdf'), 'ar', 'en')
        assert caught.value.code == 'scope_too_large' and port.creates == port.starts == 0
    finally: s.close()


class PlatformWithProgress(Platform):
    def __init__(self): super().__init__(); self.reads = 0
    def start(self, job_id): self.starts += 1  # the job keeps running
    def progress(self, job_id):
        self.reads += 1
        return {'percent': 35, 'stage': 'audit', 'chunk': 2, 'chunks': 3, 'steps': []}


def test_a_running_launch_shows_the_kitabs_progress_and_reads_it_at_most_every_10_seconds(tmp_path):
    port = PlatformWithProgress()
    s = service(tmp_path, port)
    try:
        submit(s)
        for _ in range(100):
            if s.status('r')['status'] == 'running': break
            time.sleep(.01)
        first = s.status('r')
        assert first['progress']['percent'] == 35 and first['progress']['chunk'] == 2
        s.status('r')
        assert port.reads == 1
    finally: s.close()


def test_the_kitabs_source_is_repaired_and_b_stays_bound_to_the_repaired_source(tmp_path):
    cls = importlib.import_module('independent_judge.application.pipeline_b').PipelineBService
    repo = importlib.import_module('independent_judge.infrastructure.pipeline_jobs').PipelineJobs(tmp_path)
    port = PlatformSource()
    s = cls(repo, port, OrderDamagedPdf(), None, lambda text: text.replace('الله', 'لله'))
    try:
        s.submit('pdf', Upload(b'1', 'book.pdf', 'application/pdf'), 'ar', 'en')
        done = wait(s, 'pdf')
        assert done['source'] == 'لله أكبر' and done['source_sha256'] == text_hash('لله أكبر')
        assert done['result']['source_sha256'] == text_hash('لله أكبر')
        assert done['result']['platform_source_sha256'] == text_hash('الله أكبر')
        # The edit journal of the launch belongs to the same repaired source.
        assert done['result']['processing']['source_sha256'] == text_hash('لله أكبر')
    finally: s.close()


class PlatformWithTypeset(Platform):
    def __init__(self): super().__init__(); self.orders = 0
    def typeset(self, job_id): self.orders += 1; return 'export_1'
    def typeset_status(self, export_id): return 'done'


def test_a_completed_launch_orders_one_typeset_pdf_and_follows_it(tmp_path):
    port = PlatformWithTypeset()
    s = service(tmp_path, port)
    try:
        submit(s)
        done = wait(s)
        assert done['status'] == 'completed'
        assert s.status('r')['typeset'] == {'export_id': 'export_1', 'status': 'done'}
        s.status('r')
        assert port.orders == 1
    finally: s.close()


def test_the_typeset_pdf_is_served_and_pasted_text_keeps_screen_line_breaks(tmp_path):
    from fastapi.testclient import TestClient
    from independent_judge.api.app import create_app
    class Port(PlatformWithTypeset):
        def typeset_file(self, export_id): return b'%PDF-1.7 book'
        def upload(self, source, source_language, target_language, original=None):
            self.source = source; return 'doc'
    port = Port()
    s = service(tmp_path, port)
    with TestClient(create_app(tmp_path, pipeline=s)) as client:
        assert client.get('/api/pipeline-b/none/typeset.pdf').status_code == 422
        client.post('/api/pipeline-b', data={'request_id': 'web', 'source_kind': 'text', 'source_value': 'سطر\r\nسطر',
                                             'source_language': 'ar', 'target_language': 'en'})
        wait(s, 'web'); s.status('web')
        pdf = client.get('/api/pipeline-b/web/typeset.pdf')
        assert pdf.status_code == 200 and pdf.content == b'%PDF-1.7 book'
        assert pdf.headers['content-type'] == 'application/pdf'
    assert port.source == 'سطر\nسطر'
