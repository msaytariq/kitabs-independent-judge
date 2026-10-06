"""Read saved examples or prepare an unmeasured view; no provider dependency."""
from independent_judge.comparison_ports import ComparisonCatalog, ComparisonRenderer
from independent_judge.ports import ScopeRepository
from independent_judge.domain.errors import InputError
from independent_judge.domain.comparison_summary import summarize_comparison
from independent_judge.domain.apparatus_evidence import apparatus_evidence
from independent_judge.domain.source_review import source_review
from independent_judge.domain.effort_forecast import forecast_effort
from independent_judge.domain.ratings import comparison_ratings
from independent_judge.domain.decision_effort import decision_effort
from independent_judge.domain.processing_effort import processing_effort
from independent_judge.domain.rubric_result import VERSION as RUBRIC_VERSION
from independent_judge.domain.reference_coverage import coverage_counts
from independent_judge.domain.case_study import case_study
from independent_judge.domain.jury_points import effort_reduction, jury_summary, jury_table, second_opinion
from independent_judge.application.local_evaluation import reference_key


def _view(record: dict) -> dict:
    run = record.get('run')
    manifest = run.get('manifest', {}) if run else {}
    rubric_protocol = manifest.get('protocol_version') == RUBRIC_VERSION
    # A rubric run stores no legacy findings; counting them would show false zeros.
    summary = summarize_comparison(record | {'run': None} if rubric_protocol else record)
    rubric = run.get('rubric') if rubric_protocol and run['status'] == 'completed' else None
    coverage = coverage_counts(record.get('hadith'), record.get('coverage') or (run or {}).get('coverage'))
    processing = processing_effort(record)
    takhrij = (record.get('hadith') or {}).get('takhrij')
    jury = jury_table(rubric, coverage, takhrij)
    return {key: record.get(key) for key in (
        'id', 'title', 'description', 'scope', 'provenance', 'boundary_review',
        'apparatus', 'references', 'matched_example_id')} | {
        'summary': summary,
        'demonstration': record.get('demonstration') is True,
        'effort': forecast_effort(summary),
        'ratings': comparison_ratings(record, summary),
        'decision_effort': decision_effort(record, summary),
        'processing_effort': processing,
        'rubric': rubric,
        'rubric_protocol': rubric_protocol,
        'reference_coverage': coverage,
        'jury': jury,
        'effort_reduction': effort_reduction(rubric, coverage, processing, takhrij),
        'takhrij': takhrij,
        'jury_summary': jury_summary(jury),
        'case_study': case_study(rubric, processing),
        'second_judge': second_opinion(rubric, ', '.join(manifest.get('actual_models', [])), record.get('second_judge')),
        'structural': run.get('structural') if run else None,
        'hadith': record.get('hadith'),
        'generated_apparatus': apparatus_evidence(record.get('capability_evidence'), record['scope']),
        'source_review': source_review(record),
        'run': {'id': run['id'], 'status': run['status'],
                'model': ', '.join(manifest.get('actual_models', [])),
                'code_sha': manifest.get('code_sha'),
                'protocol': manifest.get('protocol_version'),
                'cost': run.get('cost'),
                'effective_parameters': manifest.get('effective_parameters'),
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
        newer = self.jobs.reference(reference_key(record['scope'])) if self.jobs else None
        if newer or 'hadith' not in record:
            # The reference key covers the texts, so a takhrij saved for them stays valid
            # when a newer check from an earlier code version has none.
            saved = (record.get('hadith') or {}).get('takhrij')
            if newer and saved and not newer.get('takhrij'):
                newer = newer | {'takhrij': saved}
            record = record | {'hadith': newer}
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
                  'apparatus': {'a': [], 'b': []}, 'processing': scope.get('processing'), 'run': None}
        job = self.jobs.get(scope_id) if self.jobs else None
        if job and job['report']:
            return self.project(record | {'run': job['report']})
        if scope['status'] == 'ready':
            for saved in self.catalog.records():
                if saved.get('run') and all(scope[key] == saved['scope'][key] for key in (
                        'texts', 'hashes', 'profile', 'source_language', 'target_language')):
                    # Reuse only the saved judge evidence; execution time belongs to this scope's own job.
                    record = saved | {'id': scope_id, 'scope': scope, 'matched_example_id': saved['id'],
                                      'processing': scope.get('processing'),
                                      'capability_evidence': None, 'source_review': None}
                    break
        return self.project(record)
