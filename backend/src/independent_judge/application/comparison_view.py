"""Read saved examples or prepare an unmeasured view; no provider dependency."""
from independent_judge.comparison_ports import ComparisonCatalog, ComparisonRenderer
from independent_judge.ports import ScopeRepository
from independent_judge.domain.errors import InputError
from independent_judge.domain.comparison_summary import summarize_comparison
from independent_judge.domain.apparatus_evidence import apparatus_evidence
from independent_judge.domain.source_review import source_review
from independent_judge.domain.effort_forecast import forecast_effort
from independent_judge.application.local_evaluation import reference_key


def _view(record: dict) -> dict:
    summary = summarize_comparison(record)
    run = record.get('run')
    manifest = run.get('manifest', {}) if run else {}
    return {key: record.get(key) for key in (
        'id', 'title', 'description', 'scope', 'provenance', 'boundary_review',
        'apparatus', 'references', 'matched_example_id')} | {
        'summary': summary,
        'effort': forecast_effort(summary),
        'hadith': record.get('hadith'),
        'generated_apparatus': apparatus_evidence(record.get('capability_evidence'), record['scope']),
        'source_review': source_review(record),
        'run': {'id': run['id'], 'status': run['status'],
                'model': ', '.join(manifest.get('actual_models', [])),
                'code_sha': manifest.get('code_sha'),
                'calls': len(run.get('calls', [])),
                'independence': manifest.get('translator_independence', {}),
                'report_sha256': record.get('report_sha256')} if run else None,
        'live_enabled': False,
    }


class ComparisonViewService:
    def __init__(self, catalog: ComparisonCatalog, scopes: ScopeRepository, renderer: ComparisonRenderer, jobs=None):
        self.catalog, self.scopes, self.renderer = catalog, scopes, renderer
        self.jobs = jobs

    def project(self, record):
        if self.jobs:
            record = record | {'hadith': self.jobs.reference(reference_key(record['scope']))}
        return _view(record)

    def report(self, kind: str, identifier: str) -> str:
        return self.renderer(self.example(identifier) if kind == 'example' else self.scope(identifier))

    def examples(self) -> list[dict]:
        return [{'id': r['id'], 'title': r['title'], 'description': r.get('description', ''),
                 'has_report': bool(r.get('run')), 'has_source_review': bool(r.get('source_review'))}
                for r in self.catalog.records()]

    def example(self, example_id: str) -> dict:
        record = self.catalog.get(example_id)
        if record is None: raise InputError('example_not_found', 'Пример не найден.')
        return self.project(record)

    def scope(self, scope_id: str) -> dict:
        scope = self.scopes.get(scope_id)
        if scope is None: raise InputError('scope_not_found', 'Материалы не найдены.')
        record = {'id': scope_id, 'scope': scope, 'title': 'Ваши материалы',
                  'description': 'Оригинал и два перевода сохранены локально.',
                  'provenance': {'a': 'Перевод A', 'b': 'Перевод B'},
                  'apparatus': {'a': [], 'b': []}, 'run': None}
        job = self.jobs.get(scope_id) if self.jobs else None
        if job and job['report']:
            return self.project(record | {'run': job['report']})
        if scope['status'] == 'ready':
            for saved in self.catalog.records():
                if saved.get('run') and all(scope[key] == saved['scope'][key] for key in (
                        'texts', 'hashes', 'profile', 'source_language', 'target_language')):
                    record = saved | {'id': scope_id, 'scope': scope, 'matched_example_id': saved['id'],
                                      'capability_evidence': None, 'source_review': None}
                    break
        return self.project(record)
