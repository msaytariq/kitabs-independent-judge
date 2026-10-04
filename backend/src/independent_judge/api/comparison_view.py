"""Thin read-only comparison and report routes."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from independent_judge.application.comparison_view import ComparisonViewService


def build_comparison_router(service: ComparisonViewService) -> APIRouter:
    router = APIRouter(tags=['comparison'])

    @router.get('/api/examples')
    def examples(): return service.examples()

    @router.get('/api/examples/{example_id}')
    def example(example_id: str): return service.example(example_id)

    @router.get('/api/scopes/{scope_id}/comparison')
    def comparison(scope_id: str): return service.scope(scope_id)

    @router.get('/api/examples/{example_id}/report.html', response_class=HTMLResponse)
    def example_report(example_id: str): return service.report('example', example_id)

    @router.get('/api/scopes/{scope_id}/report.html', response_class=HTMLResponse)
    def scope_report(scope_id: str): return service.report('scope', scope_id)

    return router
