"""Small input invariants shared by editorial domain responsibilities."""
from math import isfinite
from independent_judge.domain.errors import InputError


def require(condition, message, code='invalid_editorial_action'):
    if not condition:
        raise InputError(code, message)


def text(value, label, limit=2000):
    require(isinstance(value, str) and bool(value.strip()) and len(value)<=limit,
            f'{label} must be nonempty text, at most {limit} characters.')
    return value.strip()


def side(state, role):
    require(role in ('a','b'), 'Select version A or B.')
    return state['sides'][role]


def current(document, expected):
    version=document['versions'][-1]
    require(version['sha256']==expected, 'The text changed. Reload before deciding.', 'stale_text')
    return version


def seconds(value):
    require(type(value) in (int,float) and 0<=value<=31536000 and isfinite(value),
            'Time must be a finite nonnegative number, up to one year.')
    return value
