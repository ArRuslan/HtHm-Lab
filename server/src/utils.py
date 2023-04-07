from functools import wraps


def getSession(f):
    @wraps(f)
    async def wrapped(*args, **kwargs):
        session = ...
        kwargs["session"] = session
        return await f(*args, **kwargs)

    return wrapped
