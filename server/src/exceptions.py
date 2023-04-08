class RequestError(Exception):
    code: int

    def __init__(self, message: str, code: int=None):
        if code is not None:
            self.code = code
        self.message = message


class ValidateError(RequestError):
    code = 400


class AuthError(RequestError):
    code = 401
