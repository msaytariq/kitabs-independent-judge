"""Optional platform boundary. No platform database or SDK imports."""
from typing import Protocol


class PipelineResultReader(Protocol):
    def completed(self, job_id: str, source_sha256: str) -> dict: ...
