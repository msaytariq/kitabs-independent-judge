"""Reviewed pilot routes and dated prices; unknown configurations fail closed."""
from independent_judge.domain.evaluation import EvaluationError


# Rates are USD per million tokens. Reserve input includes provider headroom.
# Gemini source: https://vercel.com/ai-gateway/models/gemini-3.8-flash
_PROFILES = {
    ('anthropic/claude-sonnet-5.5', 'anthropic'): (
        ('2', '10', '2.5', 'vercel-anthropic-2026-10-04'), ('medium',)),
    ('google/gemini-3.8-flash', 'google'): (
        ('0.75', '3.75', '0.825', 'vercel-google-2026-10-05'), ('low', 'high')),
}


def validate_config(config):
    if any(type(getattr(config, name)) is not str for name in (
            'model', 'provider', 'reasoning_effort', 'input_usd_per_million',
            'output_usd_per_million', 'reserve_input_usd_per_million', 'price_version')):
        raise EvaluationError('invalid_config', 'Judge model and price fields must be strings.')
    profile = _PROFILES.get((config.model, config.provider))
    if profile is None:
        raise EvaluationError('unreviewed_model', 'Judge model and provider require a reviewed route.')
    prices, efforts = profile
    if (config.input_usd_per_million, config.output_usd_per_million,
            config.reserve_input_usd_per_million, config.price_version) != prices:
        raise EvaluationError('unreviewed_price', 'Pilot pricing requires a reviewed configuration.')
    if config.reasoning_effort not in efforts:
        raise EvaluationError('unreviewed_reasoning', 'Reasoning effort is not reviewed for this model.')
    if type(config.max_tokens) is not int or not 1 <= config.max_tokens <= 8192:
        raise EvaluationError('pilot_bounds', 'Pilot output exceeds reviewed cost bounds.')
