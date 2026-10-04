"""Provider-independent evaluation contracts and explicit failures."""
from dataclasses import dataclass, field
from decimal import Decimal


class EvaluationError(RuntimeError):
    def __init__(self, code: str, message: str, *, raw: dict | None = None):
        self.code, self.raw = code, raw
        super().__init__(message)


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str
    version: str


@dataclass(frozen=True)
class JudgeConfig:
    model: str = 'anthropic/claude-sonnet-5.5'
    provider: str = 'anthropic'
    max_tokens: int = 4096
    reasoning_effort: str = 'medium'
    input_usd_per_million: str = '2'
    output_usd_per_million: str = '10'
    # Cache writes may exceed the uncached input price; reserve conservatively.
    reserve_input_usd_per_million: str = '2.5'
    price_version: str = 'vercel-anthropic-2026-10-04'


@dataclass(frozen=True)
class LlmResult:
    text: str
    actual_model: str
    usage: dict
    cost_usd: Decimal
    raw: dict = field(repr=False)
