"""Run/status and automatic reference checks, loopback-guarded by the app."""
from fastapi import APIRouter


def build_run_router(evaluation, view):
    router = APIRouter(tags=['local-evaluation'])

    @router.get('/api/runtime')
    def runtime():
        return {'live_enabled': evaluation.runtime is not None, 'local_only': True}

    @router.post('/api/scopes/{scope_id}/run', status_code=202)
    def run(scope_id: str): return evaluation.submit(scope_id)

    @router.get('/api/scopes/{scope_id}/run')
    def status(scope_id: str): return evaluation.status(scope_id)

    @router.post('/api/scopes/{scope_id}/references')
    def scope_references(scope_id: str):
        return evaluation.references(view.scope(scope_id)['scope'])

    @router.post('/api/examples/{example_id}/references')
    def example_references(example_id: str):
        return evaluation.references(view.example(example_id)['scope'])

    return router
