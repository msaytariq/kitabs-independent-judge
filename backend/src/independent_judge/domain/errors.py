"""Actionable application failures, translated to HTTP at the API boundary."""


class InputError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)
