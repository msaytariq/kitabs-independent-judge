"""External workspace handoff and verified result retrieval are separate actions."""
from urllib.parse import urlsplit
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash
from independent_judge.pipeline_ports import PipelineResultReader


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
