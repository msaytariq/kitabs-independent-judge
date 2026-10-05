"""Prepare and persist a preview only; preparation never calls a model."""
from dataclasses import asdict
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import TextRange, prepare_scope
from independent_judge.ports import ComparisonRepository, ScopeRepository


class ScopeService:
    def __init__(self, inputs: ComparisonRepository, scopes: ScopeRepository, pipeline_jobs=None):
        self.inputs, self.scopes = inputs, scopes
        self.pipeline_jobs = pipeline_jobs

    def create(self, comparison_id: str, ranges: dict[str, TextRange], profile: str, confirmed: bool, *, pipeline_request_id=None):
        comparison = self.inputs.get(comparison_id)
        if comparison is None:
            raise InputError('comparison_not_found', 'Comparison not found.')
        i = comparison.inputs
        prepared = prepare_scope(i, ranges['source'], ranges['a'], ranges['b'],
                                 i.source_language, i.target_language, profile, confirmed=confirmed)
        extra = {}
        if pipeline_request_id:
            if not self.pipeline_jobs:
                raise InputError('pipeline_not_found', 'Pipeline connection is not configured.')
            saved = self.pipeline_jobs.get(pipeline_request_id)
            result = saved.get('result')
            if (saved['status'] != 'completed' or not result
                    or result['source_sha256'] != prepared.hashes['source'] or result['sha256'] != prepared.hashes['b']
                    or saved['source_language'] != i.source_language or saved['target_language'] != i.target_language):
                raise InputError('pipeline_source_mismatch', 'The source or B differs from the completed pipeline result.')
            extra = {'pipeline': {k: result.get(k) for k in ('job_id', 'assembly_inputs', 'chunk_count', 'platform_artifact_hash')},
                     'processing': {'b': result.get('processing')}, 'pipeline_request_id': pipeline_request_id}
        return self.scopes.create({'comparison_id': comparison_id, **asdict(prepared), **extra})

    def get(self, scope_id: str):
        result = self.scopes.get(scope_id)
        if result is None:
            raise InputError('scope_not_found', 'Scope not found.')
        return result
