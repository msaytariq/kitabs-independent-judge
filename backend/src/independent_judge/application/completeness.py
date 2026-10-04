"""Build one common inventory and judge each version twice against it."""
from independent_judge.domain.completeness import (Unit,Coverage,parse_units,inventory_prompt,
    coverage_prompt,validate_inventory,reconcile_coverage)


def assess_completeness(scope,call):
    units=parse_units(call('source-inventory',inventory_prompt(scope)),Unit)
    inventory=validate_inventory(units,scope.texts['source'])
    result={'inventory':inventory}
    for side in ('a','b'):
        passes=[parse_units(call(f'coverage-{i}-{side}',coverage_prompt(scope,side,units)),Coverage,len(units)) for i in range(2)]
        result[side]=reconcile_coverage(passes,scope.texts[side])
    return result
