"""Read the existing authenticated KITABS contract; never start paid work here."""
import re
from urllib.parse import urlsplit
import httpx
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash


class KitabsPipeline:
    def __init__(self, api_origin: str, token: str, *, transport=None):
        parsed = urlsplit(api_origin)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
            raise ValueError('Explicit HTTPS API origin is required.')
        self.origin, self.token, self.transport = api_origin.rstrip('/'), token, transport

    def completed(self, job_id: str, source_sha256: str) -> dict:
        if not self.token:
            raise InputError('pipeline_auth_required', 'Use the authenticated KITABS workspace or configure a local operator adapter.')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', job_id):
            raise InputError('invalid_job_id', 'Invalid pipeline job identifier.')
        try:
            with httpx.Client(base_url=self.origin + '/', transport=self.transport, timeout=20,
                              follow_redirects=False, trust_env=False,
                              headers={'Authorization': 'Bearer ' + self.token}) as client:
                job = self._get(client, f'pipeline/jobs/{job_id}')['job']
                if job['id'] != job_id or job['status'] != 'completed':
                    raise InputError('pipeline_unfinished', 'The platform job has no completed B result.')
                response = self._get(client, f'pipeline/jobs/{job_id}/assembly')
            return _result(response, job_id, source_sha256)
        except InputError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise InputError('pipeline_unavailable', 'Cannot verify the platform result. Use a completed B file.') from exc

    @staticmethod
    def _get(client, path):
        with client.stream('GET', path) as response:
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
            'mode': 'unverified', 'state': 'completed'}


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
