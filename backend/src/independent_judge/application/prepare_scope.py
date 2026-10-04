"""Prepare and persist a preview only; preparation never calls a model."""
from dataclasses import asdict
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import TextRange, prepare_scope
from independent_judge.ports import ComparisonRepository, ScopeRepository


class ScopeService:
    def __init__(self, inputs: ComparisonRepository, scopes: ScopeRepository):
        self.inputs, self.scopes = inputs, scopes

    def create(self, comparison_id: str, ranges: dict[str, TextRange], profile: str, confirmed: bool):
        comparison = self.inputs.get(comparison_id)
        if comparison is None:
            raise InputError('comparison_not_found', 'Comparison not found.')
        i = comparison.inputs
        prepared = prepare_scope(i, ranges['source'], ranges['a'], ranges['b'],
                                 i.source_language, i.target_language, profile, confirmed=confirmed)
        return self.scopes.create({'comparison_id': comparison_id, **asdict(prepared)})

    def get(self, scope_id: str):
        result = self.scopes.get(scope_id)
        if result is None:
            raise InputError('scope_not_found', 'Scope not found.')
        return result
