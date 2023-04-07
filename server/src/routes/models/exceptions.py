class RequestError(BaseException):
    code: int
    message: str


class ValidateError(RequestError):
    code = 400

    def __init__(self, message: str):
        self.message = message