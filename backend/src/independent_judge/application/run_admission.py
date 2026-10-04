"""Reserve before every request, record raw receipt, then reconcile reported spend."""
from dataclasses import asdict
from datetime import datetime,timezone
from independent_judge.domain.budget import reservation
from independent_judge.domain.evaluation import EvaluationError
from independent_judge.domain.run_manifest import digest
from independent_judge.evaluation_ports import JudgePort,BudgetPort,RunPort


class AdmittedCalls:
    def __init__(self,judge:JudgePort,budget:BudgetPort,repository:RunPort,run_id,config,on_progress=None):
        self.judge,self.budget,self.repository=judge,budget,repository
        self.run_id,self.config,self.on_progress=run_id,config,on_progress
        self.calls=[]

    def __call__(self,call_id,prompt):
        self.budget.reserve(self.run_id,call_id,reservation(prompt,self.config))
        record={'call_id':call_id,'prompt_version':prompt.version,'prompt_sha256':digest(asdict(prompt)),
                'prompt':asdict(prompt),'started_at':datetime.now(timezone.utc).isoformat()}
        if self.on_progress: self.on_progress(call_id,'started',self.budget.summary(self.run_id))
        try:
            result=self.judge.complete(prompt,self.config)
        except EvaluationError as exc:
            record.update(error={'code':exc.code,'message':str(exc)},raw=exc.raw)
            self.repository.receipt(self.run_id,call_id,record)
            self.calls.append({k:v for k,v in record.items() if k not in ('prompt','raw')})
            # A priced but truncated response is still a paid response.
            if exc.cost_usd is not None:
                self.budget.settle(self.run_id,call_id,exc.cost_usd)
            raise
        record.update(raw=result.raw,actual_model=result.actual_model,usage=result.usage,
                      cost_usd=str(result.cost_usd),finished_at=datetime.now(timezone.utc).isoformat())
        self.repository.receipt(self.run_id,call_id,record)
        self.calls.append({k:v for k,v in record.items() if k not in ('prompt','raw')})
        self.budget.settle(self.run_id,call_id,result.cost_usd)
        if self.on_progress: self.on_progress(call_id,'finished',self.budget.summary(self.run_id))
        return result.text
