"""Conservative admission estimates in integer millionths of a US dollar."""
from decimal import Decimal, ROUND_CEILING
import json
from independent_judge.domain.evaluation import EvaluationError


def micros(amount: Decimal) -> int:
    if not amount.is_finite() or amount < 0:
        raise EvaluationError('invalid_budget','Budget values must be finite and nonnegative.')
    return int((amount*1000000).to_integral_value(rounding=ROUND_CEILING))


def usd(amount: int) -> str:
    return f'{Decimal(amount)/1000000:.6f}'


def reservation(prompt, config) -> Decimal:
    if (config.model, config.provider, config.input_usd_per_million,
            config.output_usd_per_million, config.reserve_input_usd_per_million,
            config.price_version) != ('anthropic/claude-sonnet-5.5','anthropic','2','10','2.5',
                                     'vercel-anthropic-2026-10-04'):
        raise EvaluationError('unreviewed_price','Pilot model and pricing require a reviewed configuration.')
    # UTF-8 byte count is deliberately much larger than normal token counts.
    # Add framing headroom and 25% price/token buffer; no tools or long-context tiers.
    schema_bytes=len(json.dumps(prompt.response_schema,ensure_ascii=False).encode('utf-8'))
    input_bound=len((prompt.system+prompt.user).encode('utf-8'))+schema_bytes+2048
    if input_bound > 100000 or not 1 <= config.max_tokens <= 8192:
        raise EvaluationError('pilot_bounds','Pilot request exceeds reviewed cost bounds.')
    return (Decimal(input_bound)*Decimal(config.reserve_input_usd_per_million)
            +Decimal(config.max_tokens)*Decimal(config.output_usd_per_million))*Decimal('1.25')/1000000 + Decimal('0.001')
