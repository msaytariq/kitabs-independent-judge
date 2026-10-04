"""Coordinate confirmed scopes, pure editorial rules and transactional storage."""
from time import time_ns
from uuid import uuid4
from independent_judge.domain.errors import InputError
from independent_judge.domain.editorial_validation import require
from independent_judge.domain.editorial_work import new_review,apply_command
from independent_judge.editorial_ports import EditorialRepository
from independent_judge.ports import ScopeRepository

LIMITATIONS=[
    'Local operator stand; editor labels are self-declared, not authenticated identities.',
    'Timer records operator-declared intervals, not attention. Pause during breaks; a closed tab does not stop it.',
    'Prior work is an attributed self-report. Unknown history blocks total time-saving claims.',
    'Publication acceptance and task decisions are human attestations, not independently certified outcomes.',
    'This workbench makes no LLM calls and does not verify Quran editions or perform exhaustive takhrij.',
]


class EditorialService:
    def __init__(self,scopes:ScopeRepository,repository:EditorialRepository):
        self.scopes,self.repository=scopes,repository
        self.clock=lambda:time_ns()//1000000

    def create(self,scope_id,rubric,actor):
        scope=self.scopes.get(scope_id)
        if scope is None: raise InputError('scope_not_found','Scope not found.')
        state=new_review(scope,rubric,actor,uuid4().hex,self.clock())
        return self.repository.create(state,{'kind':'create','actor':actor,'command_id':uuid4().hex,
                                             'params':{'scope_id':scope_id,'rubric':rubric}})

    def get(self,ident):
        state=self.repository.get(ident)
        if state is None: raise InputError('review_not_found','Editorial review not found.')
        return state

    def command(self,ident,command):
        previous=self.repository.previous_command(ident,command)
        if previous is not None: return previous
        state=self.get(ident)
        require(state['revision']==command['expected_revision'],
                'Review changed in another tab. Reload before continuing.','editorial_conflict')
        result=apply_command(state,command,self.clock())
        return self.repository.append(result,state['revision'],command)

    def export(self,ident):
        # Stable cutoff: concurrent later events are not mixed with an older snapshot.
        state=self.get(ident)
        return {'format':'editorial-evidence-v1','state':state,
                'events':[e for e in self.repository.events(ident) if e['revision']<=state['revision']],
                'limitations':LIMITATIONS}
