"""External workspace handoff and verified result retrieval are separate actions."""
from urllib.parse import urlsplit
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash
from independent_judge.pipeline_ports import PipelineResultReader
from independent_judge.pipeline_ports import PipelinePort
from concurrent.futures import ThreadPoolExecutor
import base64
import re


def handoff(source: str, mode: str, web_origin: str) -> dict:
    if mode not in ('autopilot', 'manual'):
        raise InputError('invalid_pipeline_mode', 'Select autopilot or manual mode.')
    origin = urlsplit(web_origin)
    if origin.scheme != 'https' or not origin.hostname or origin.username or origin.query or origin.fragment:
        raise InputError('invalid_pipeline_origin', 'Configure the KITABS HTTPS web origin.')
    source_hash = text_hash(source)
    return {'id': text_hash(source_hash + ':' + mode), 'source_sha256': source_hash,
            'mode': mode, 'state': 'external_workflow', 'job_started': False,
            'workspace_url': web_origin.rstrip('/') + '/workspace'}


def completed_b(reader: PipelineResultReader, job_id: str, source_sha256: str) -> dict:
    return reader.completed(job_id, source_sha256)


class PipelineBService:
    def __init__(self, jobs, platform: PipelinePort | None, extractor, max_requests: int | None = None):
        self.jobs, self.platform, self.extractor = jobs, platform, extractor
        self.max_requests = max_requests
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='pipeline-b')

    def remaining(self):
        if not self.platform or self.max_requests is None:
            return None
        return max(0, self.max_requests - self.jobs.count())

    def close(self):
        self.executor.shutdown(wait=True)

    def submit(self, request_id, upload, source_language, target_language):
        if not self.platform:
            raise InputError('pipeline_disabled', 'The operator has not enabled the pipeline connection.')
        if not re.fullmatch('[A-Za-z0-9_-]{1,80}', request_id):
            raise InputError('invalid_pipeline_id', 'Invalid request ID.')
        if (source_language, target_language) != ('ar', 'en'):
            raise InputError('language_mismatch', 'Embedded translation currently supports Arabic to English.')
        if len(upload.content) > 20 * 1024 * 1024:
            raise InputError('file_too_large', 'File exceeds 20 MiB.')
        extracted = self.extractor.extract(upload.content, upload.filename, upload.content_type)
        source = extracted.text
        if not source.strip() or len(source) > 18000 or (extracted.page_count or 0) > 10:
            raise InputError('scope_too_large', 'Use a nonempty source of at most 18000 characters and 10 PDF pages.')
        packet = {'id': request_id, 'source': source, 'source_sha256': text_hash(source),
                  'source_language': source_language, 'target_language': target_language,
                  'original': {'filename': upload.filename, 'content_type': upload.content_type,
                               'content_base64': base64.b64encode(upload.content).decode()},
                  'warnings': list(extracted.warnings), 'status': 'queued', 'job_id': None,
                  'document_id': None, 'result': None, 'error': None}
        saved, inserted = self.jobs.claim(request_id, packet, self.max_requests)
        if inserted:
            self.executor.submit(self._execute, saved)
        return self._public(saved)

    def _execute(self, packet):
        key = packet['id']
        try:
            self.jobs.update(key, status='uploading')
            doc = self.platform.upload(packet['source'], packet['source_language'], packet['target_language'])
            self.jobs.update(key, status='creating', document_id=doc)
            job = self.platform.create(doc)
            # Commit the known job before the only paid start attempt.
            self.jobs.update(key, status='running', job_id=job)
            self.platform.start(job)
            self.status(key)
        except Exception:
            self.jobs.update(key, status='uncertain', error='pipeline_response_uncertain')
            # Subsequent polling may recover a known job, but never POST again.

    def status(self, request_id):
        packet = self.jobs.get(request_id)
        if self.platform and packet['job_id'] and packet['status'] in ('running', 'uncertain'):
            try:
                job = self.platform.status(packet['job_id'])
                if job['status'] == 'completed':
                    result = self.platform.completed(packet['job_id'], packet['source_sha256'])
                    self.jobs.update(request_id, status='completed', result=result, error=None)
                elif job['status'] in ('failed', 'cancelled', 'paused', 'waiting_review'):
                    self.jobs.update(request_id, status='failed', error='pipeline_' + job['status'])
            except InputError:
                pass
        return self._public(self.jobs.get(request_id))

    @staticmethod
    def _public(packet):
        return {k: v for k, v in packet.items() if k != 'original'}
