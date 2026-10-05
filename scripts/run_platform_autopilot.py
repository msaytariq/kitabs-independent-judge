"""Run the real local platform on a private DB copy through the shared USD ledger.

Execute with the platform Python environment and this repository on PYTHONPATH.
No platform source changes, customer-account charges, mail, OCR or deployment.
"""
import argparse
import asyncio
from dataclasses import asdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from independent_judge.infrastructure.budget_repository import BudgetLedger
from independent_judge.infrastructure.platform_budget_transport import BudgetedGatewayTransport


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + '\n')


def copy_database(source, destination):
    if destination.exists(): return
    with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as original:
        with sqlite3.connect(destination) as copied:
            original.backup(copied)


async def run(args):
    sys.path.insert(0, str(args.platform_root / 'backend/src'))
    from kitabai.config import Settings, load_local_dotenv
    from kitabai.application.runtime import reset_runtime
    from kitabai.application.runtime_storage import close_runtime_storage
    from kitabai.application.runtime_ocr import create_lazy_ocr_client
    from kitabai.application.request_context import set_brand
    from kitabai.application.services.document_uploads import MockUploadMetadata, MockUploadFile
    from kitabai.application.services.documents import upload_document
    from kitabai.application.services.pipeline import create_job
    from kitabai.application.services.pipeline_stream import _build_streamer
    from kitabai.application.serializers import serialize_artifact
    from kitabai.infrastructure.llm.vercel_gateway import VercelAiGatewayLlmClient
    from kitabai.domain.artifacts.models import AssembledDocumentPayload

    args.work_dir.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(args.source.read_bytes()).hexdigest()
    database = args.work_dir / 'platform.sqlite3'
    if database.resolve() == args.source_db.resolve():
        raise ValueError('Output must be an isolated database copy')
    copy_database(args.source_db, database)
    budget = BudgetLedger(args.budget_dir, total_usd=Decimal('1'), per_run_usd=Decimal('1'))
    rates = json.loads(args.rates.read_text())['rates']
    def progress(call_id, state, usage):
        print(json.dumps({'call': call_id, 'state': state, 'budget': usage}), flush=True)
    transport = BudgetedGatewayTransport(budget, args.work_dir, args.run_id, rates, on_progress=progress)
    secrets = {}
    load_local_dotenv(environ=secrets, start_path=args.platform_root)
    key = secrets.get('AI_GATEWAY_API_KEY') or secrets.get('VERCEL_AI_GATEWAY_KEY', '')
    if args.live and not key: raise ValueError('Project Gateway key is missing')
    client = VercelAiGatewayLlmClient(key, 'https://ai-gateway.vercel.sh/v1', transport=transport)
    settings = Settings.from_env({'DATABASE_URL': 'sqlite:///' + str(database.resolve()),
        'KITABAI_RUNTIME_STORAGE': 'sqlite', 'KITABAI_LLM_CLIENT': 'vercel_gateway',
        'AI_GATEWAY_API_KEY': key, 'KITABAI_OCR_CLIENT': 'mistral'})
    runtime = reset_runtime(settings, llm_client=client, ocr_client=create_lazy_ocr_client(settings))
    set_brand('io')
    state_path = args.work_dir / 'state.json'
    try:
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state['source_sha256'] != source_hash or state['run_id'] != args.run_id:
                raise ValueError('Existing run must retain its source and identity')
            if state.get('status') == 'completed':
                output = args.work_dir / 'b.txt'
                if hashlib.sha256(output.read_bytes()).hexdigest() != state['b_sha256']:
                    raise ValueError('Completed B output changed')
                print(json.dumps({'status': 'already_completed', 'budget': budget.summary()}), flush=True)
                return
        else:
            uploaded = await upload_document(MockUploadMetadata(
                title=args.title, source_format='txt', source_lang='ar', target_lang='en',
                is_scanned_pdf=False, file=MockUploadFile(args.source.name, 'text/plain', args.source.read_bytes())))
            document_id = uploaded['document']['id']
            result = await create_job(document_id)
            state = {'document_id': document_id, 'job_id': result['job']['id'],
                'run_id': args.run_id, 'source_sha256': source_hash,
                'platform_commit': subprocess.check_output(['git', '-C', str(args.platform_root),
                    'rev-parse', 'HEAD'], text=True).strip(),
                'environment': 'local isolated DB snapshot; not production',
                'preparation': 'deterministic pipeline preparation; no UI classifier invocation'}
            save(state_path, state)
        job = await runtime.jobs.get(state['job_id'])
        prepared = await runtime.source_preparer.prepare(job)
        state['stage_configs'] = [asdict(stage) for stage in job.stage_configs]
        state['chunks'] = len(prepared.chunks.payload.chunks)
        state['status'] = 'prepared'
        save(state_path, state)
        print(json.dumps({'job_id': job.id, 'chunks': state['chunks'],
            'models': {s.stage_id: s.model for s in job.stage_configs if s.model},
            'live': args.live, 'budget': budget.summary()}), flush=True)
        if not args.live: return
        with (args.work_dir / 'events.jsonl').open('a') as events:
            async for event in _build_streamer().stream(job.id, step=False):
                events.write(json.dumps(asdict(event), ensure_ascii=False, default=str) + '\n')
                events.flush()
                if event.event in {'stage_started', 'stage_completed', 'job_completed', 'error', 'job_blocked'}:
                    print(json.dumps({'event': event.event, 'stage': event.data.get('stageId'),
                        'message': event.data.get('message')}), flush=True)
        artifacts = await runtime.artifacts.list_for_job(job.id)
        save(args.work_dir / 'artifacts.json', [serialize_artifact(a) for a in artifacts])
        finished = await runtime.jobs.get(job.id)
        state.update(status=finished.status.value, budget=budget.summary())
        save(state_path, state)
        if finished.status.value != 'completed':
            raise RuntimeError('Platform run did not complete; saved artifacts retained')
        assemblies = [a for a in artifacts if isinstance(a.payload, AssembledDocumentPayload)]
        if len(assemblies) != 1: raise RuntimeError('Expected exactly one assembled result')
        output = assemblies[0].payload.body
        (args.work_dir / 'b.txt').write_text(output)
        state['b_sha256'] = hashlib.sha256(output.encode()).hexdigest()
        save(state_path, state)
        print(json.dumps({'status': 'completed', 'b_characters': len(output), 'budget': budget.summary()}), flush=True)
    finally:
        close_runtime_storage(runtime.storage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('platform-root', 'source-db', 'source', 'work-dir', 'budget-dir', 'rates'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--title', default='Local translation comparison')
    parser.add_argument('--live', action='store_true')
    asyncio.run(run(parser.parse_args()))
