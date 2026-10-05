"""Optional explicit task-specific platform connection; no production defaults."""
import os
from independent_judge.application.pipeline_b import PipelineBService
from independent_judge.infrastructure.pipeline_jobs import PipelineJobs
from independent_judge.infrastructure.kitabs_pipeline import KitabsPipeline
from independent_judge.infrastructure.text_extractors import LocalTextExtractor


def configured_pipeline(directory):
    port = None
    if os.environ.get('JUDGE_PIPELINE_ENABLED') == '1':
        # This flag attests that the separately running test platform uses the
        # shared per-request budget transport. Judge cannot enforce its billing.
        if os.environ.get('JUDGE_PIPELINE_BUDGET_GUARDED') != '1':
            raise ValueError('Enable the shared budget guard in the target before enabling pipeline requests.')
        port = KitabsPipeline(os.environ['JUDGE_PIPELINE_API_ORIGIN'], os.environ['JUDGE_PIPELINE_TOKEN'],
                              allow_loopback=os.environ.get('JUDGE_PIPELINE_ALLOW_LOOPBACK') == '1')
    return PipelineBService(PipelineJobs(directory), port, LocalTextExtractor())
