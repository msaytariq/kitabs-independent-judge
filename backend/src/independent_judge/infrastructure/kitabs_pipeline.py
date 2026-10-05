"""Authenticated platform API. Launch only through a durable application claim."""
import base64
import re
from datetime import datetime
from urllib.parse import urlsplit
import httpx
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash
from independent_judge.infrastructure.platform_processing import processing_packet


class _Unauthorized(Exception):
    pass


def _refuse_401(response):
    if response.status_code == 401:
        raise _Unauthorized()


class KitabsPipeline:
    def __init__(self, api_origin: str, token: str, *, transport=None, allow_loopback=False, session=None):
        parsed = urlsplit(api_origin)
        local = allow_loopback and parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1', '::1')
        if (parsed.scheme != 'https' and not local) or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
            raise ValueError('Explicit HTTPS API origin is required.')
        self.origin, self.token, self.transport = api_origin.rstrip('/'), token, transport
        self.session = session  # Access tokens expire; a session renews them with the refresh token.

    def _renew(self) -> bool:
        refresh = self.session.load() if self.session else ''
        if not refresh:
            return False
        try:
            with httpx.Client(transport=self.transport, timeout=30, follow_redirects=False, trust_env=False) as client:
                response = client.post(self.origin + '/auth/refresh', json={'refreshToken': refresh})
            if response.status_code != 200:
                return False
            pair = response.json()
            self.token = pair['accessToken']
            self.session.save(pair['refreshToken'])
            return True
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return False

    def _authorized(self, action):
        """Run action(client); renew an expired token once. A 401 means the platform did nothing."""
        if not self.token and not self._renew():
            raise InputError('pipeline_auth_required', 'Pipeline authorization is required.')
        for attempt in (1, 2):
            try:
                with self._client() as client:
                    return action(client)
            except _Unauthorized:
                if attempt == 2 or not self._renew():
                    raise InputError('pipeline_auth_required', 'KITABS authorization is required.') from None

    def _client(self, timeout=300):
        return httpx.Client(base_url=self.origin + '/', transport=self.transport, timeout=timeout,
                            follow_redirects=False, trust_env=False, event_hooks={'response': [_refuse_401]},
                            headers={'Authorization': 'Bearer ' + self.token})

    def _post(self, path, data):
        def send(client):
            response = client.post(path, json=data)
            response.raise_for_status()
            if len(response.content) > 20 * 1024 * 1024:
                raise ValueError('Response too large')
            return response.json()
        try:
            return self._authorized(send)
        except InputError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise InputError('pipeline_unavailable', 'Platform response is uncertain. Do not replay this request.') from None

    def upload(self, source, source_language, target_language):
        response = self._post('documents', {'title': 'Judge comparison', 'sourceFormat': 'txt',
            'sourceLang': source_language, 'targetLang': target_language, 'isScannedPdf': False,
            'file': {'fileName': 'judge-source.txt', 'contentType': 'text/plain',
                     'dataBase64': base64.b64encode(source.encode()).decode()}})
        return response['document']['id']

    def create(self, document_id):
        return self._post('pipeline/jobs', {'documentId': document_id})['job']['id']

    def status(self, job_id):
        self._valid_id(job_id)
        try:
            job = self._authorized(lambda client: self._get(client, f'pipeline/jobs/{job_id}'))['job']
            if job['id'] != job_id:
                raise InputError('pipeline_job_mismatch', 'Platform returned another job.')
            return job
        except InputError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise InputError('pipeline_unavailable', 'Cannot read platform status.') from None

    def start(self, job_id):
        self._valid_id(job_id)
        def run(client):
            with client.stream('POST', f'pipeline/jobs/{job_id}/start-stream', params={'step': 'false'}) as response:
                response.raise_for_status()
                for _ in response.iter_lines():
                    pass  # Platform owns the background producer; UI observes this service.
        try:
            self._authorized(run)
        except httpx.HTTPError:
            raise InputError('pipeline_unavailable', 'Autopilot response is uncertain; check the known job status.') from None

    @staticmethod
    def _valid_id(job_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', job_id):
            raise InputError('invalid_job_id', 'Invalid pipeline job identifier.')

    def completed(self, job_id: str, source_sha256: str, started_at: float | None = None) -> dict:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', job_id):
            raise InputError('invalid_job_id', 'Invalid pipeline job identifier.')
        def read(client):
            job = self._get(client, f'pipeline/jobs/{job_id}')['job']
            if job['id'] != job_id or job['status'] != 'completed':
                raise InputError('pipeline_unfinished', 'The platform job has no completed B result.')
            result = _result(self._get(client, f'pipeline/jobs/{job_id}/assembly'), job_id, source_sha256)
            try:
                result['processing'] = self._journal(client, job_id, result, started_at)
            except (InputError, httpx.HTTPError, KeyError, ValueError, TypeError):
                result['processing'] = None  # B stays valid; its time stays unknown.
            return result
        try:
            return self._authorized(read)
        except InputError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise InputError('pipeline_unavailable', 'Cannot verify the platform result. Use a completed B file.') from exc

    def _journal(self, client, job_id, result, started_at):
        """Applied audit and editor edits from the platform's own records; time from start to assembly."""
        artifacts = self._get(client, f'pipeline/jobs/{job_id}/artifacts')['artifacts']
        chunks = sorted({a['chunkId'] for a in artifacts
                         if a.get('jobId') == job_id and a['kind'] in ('audit_report', 'edited_chunk')})
        reviews = []
        for stage in ('audit', 'editor'):
            for chunk in chunks:
                answer = self._get(client, f'pipeline/jobs/{job_id}/audit-reviews',
                                   {'chunkId': chunk, 'stageId': stage})
                reviews += [{'stage_id': stage, 'chunk_id': chunk, 'issue_index': s['issueIndex'],
                             'status': s['status']} for s in answer['statuses']]
        finished = _timestamp(result.get('assembly_created_at'))
        intervals = ([{'start': started_at, 'end': finished}]
                     if started_at is not None and finished is not None and finished >= started_at else None)
        return processing_packet(job_id=job_id, artifacts=artifacts, reviews=reviews, intervals=intervals,
                                 source_sha256=result['source_sha256'], b_text=result['text'])

    @staticmethod
    def _get(client, path, params=None):
        with client.stream('GET', path, params=params) as response:
            if response.status_code in (401,403):
                raise InputError('pipeline_auth_required', 'KITABS authorization is required.')
            response.raise_for_status()
            content = bytearray()
            for block in response.iter_bytes():
                content.extend(block)
                if len(content) > 20 * 1024 * 1024:
                    raise InputError('file_too_large', 'Platform response is too large.')
            import json
            return json.loads(content)


def _timestamp(value):
    try:
        return datetime.fromisoformat(value).timestamp() if value else None
    except (TypeError, ValueError):
        return None


def _result(response, job_id, source_sha256):
    if response['jobId'] != job_id:
        raise InputError('pipeline_job_mismatch', 'The result belongs to another job.')
    artifacts = response['artifacts']
    groups = {kind: [a for a in artifacts if a['kind'] == kind and a['jobId'] == job_id]
              for kind in ('source_text', 'chunks', 'assembled_document')}
    if any(len(items) != 1 for items in groups.values()):
        raise InputError('pipeline_contract_incomplete', 'Need one source, chunk inventory and completed assembly.')
    source = groups['source_text'][0]['payload']['text']
    if text_hash(source) != source_sha256:
        raise InputError('pipeline_source_mismatch', 'Platform source differs from the selected source; review extraction boundaries.')
    assembly = groups['assembled_document'][0]
    payload = assembly['payload']
    expected = {c['id'] for c in groups['chunks'][0]['payload']['chunks']}
    inputs = payload.get('inputSources', [])
    actual = {entry['chunkId'] for entry in inputs}
    job_artifacts = [a for a in artifacts if a['jobId'] == job_id]
    known = {a['id']: a for a in job_artifacts}
    if (not expected or actual != expected or len(inputs) != len(expected)
            or len(known) != len(job_artifacts)
            or payload['jobId'] != job_id or not payload['body'].strip()
            or any(not _verified_input(s, known) for s in inputs)
            or not assembly.get('hash')):
        raise InputError('pipeline_incomplete_assembly', 'The assembly is partial or references stale artifacts.')
    return {'job_id': job_id, 'text': payload['body'], 'sha256': text_hash(payload['body']),
            'source_sha256': source_sha256, 'platform_artifact_id': assembly['id'],
            'platform_artifact_hash': assembly['hash'], 'human_work': None,
            'mode': 'unverified', 'state': 'completed',
            'processing': response.get('processingMeasurements'),
            'assembly_inputs': inputs, 'chunk_count': len(expected),
            'assembly_created_at': assembly.get('createdAt')}


def _verified_input(source: dict, known: dict) -> bool:
    """Only generated inputs can be proved by this artifact-only endpoint."""
    if any(not isinstance(source.get(key), str) or not source[key].strip()
           for key in ('artifactId', 'artifactHash', 'chunkId', 'stageId')):
        return False
    artifact = known.get(source['artifactId'])
    kinds = {'translator': 'translated_chunk', 'editor': 'edited_chunk',
             'proofreader': 'proofread_chunk'}
    return bool(artifact and source.get('sourceKind') == 'generated'
                and not source.get('revisionId') and not source.get('revisionNumber')
                and source['stageId'] in kinds
                and artifact.get('kind') == kinds[source['stageId']]
                and artifact.get('stageId') == source['stageId']
                and artifact.get('chunkId') == source['chunkId']
                and artifact.get('payload', {}).get('chunkId') == source['chunkId']
                and artifact.get('hash') == source['artifactHash'])
