"""Gateway invoice fields, including service surcharges, without double counting."""
from decimal import Decimal, InvalidOperation


def amount(value) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() and result >= 0 else None
    except InvalidOperation:
        return None


def reported_cost(raw: dict) -> Decimal | None:
    usage = raw.get('usage')
    if not isinstance(usage, dict):
        return None
    if 'gateway_cost' in usage:
        return amount(usage['gateway_cost'])
    base = amount(usage.get('cost'))
    if 'surcharge_cost' in usage:
        surcharge = amount(usage['surcharge_cost'])
        return base + surcharge if base is not None and surcharge is not None else None
    return base
