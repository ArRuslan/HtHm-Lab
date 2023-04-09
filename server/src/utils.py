from base64 import b64decode as _b64decode, b64encode as _b64encode
from functools import wraps
from hashlib import sha512
from hmac import new
from json import loads, dumps
from os import environ
from time import time
from typing import Union, Optional, Hashable, Any

from bcrypt import hashpw, gensalt, checkpw
from quart import request
from sqlalchemy import select, and_, or_

from .db import async_session
from .exceptions import AuthError, RequestError
from .models.chats import Dialog
from .models.users import Session


def getSession(f):
    @wraps(f)
    async def wrapped(*args, **kwargs):
        if not (token := request.headers.get("Authorization")) or not (data := JWT.decode(token, environ["SECRET_KEY"])):
            raise AuthError("Session does not exist or expired!")
        async with async_session() as sess:
            stmt = select(Session).where(and_(Session.id == data["session_id"], Session.user_id == data["user_id"]))
            result = (await sess.scalars(stmt)).first()
            if result is None:
                raise AuthError("Session does not exist or expired!")
        session = result
        kwargs["session"] = session
        return await f(*args, **kwargs)

    return wrapped


def getDialog(f):
    @wraps(f)
    async def wrapped(*args, **kwargs):
        if not (session := kwargs.get("session")):
            raise AuthError("Session does not exist or expired!")
        data = kwargs.get("data") or kwargs.get("query_args")
        if not data:
            raise RequestError("Unknown dialog!", 404)
        async with async_session() as sess:
            stmt = select(Dialog).where(and_(
                or_(Dialog.user_1 == session.user_id, Dialog.user_2 == session.user_id),
                Dialog.id == data.dialog_id
            ))
            dialog = (await sess.scalars(stmt)).first()
            if dialog is None:
                raise RequestError("Unknown dialog!", 404)
        kwargs["dialog"] = dialog
        return await f(*args, **kwargs)

    return wrapped


def prepPassword(password: str) -> bytes:
    password = password.encode("utf8")
    return password.replace(b"\x00", b'')


def hashPassword(password: str) -> str:
    password = prepPassword(password)
    return hashpw(password, gensalt()).decode("utf8")


def checkPassword(password: str, password_hash: str) -> bool:
    password = prepPassword(password)
    password_hash = password_hash.encode("utf8")
    return checkpw(password, password_hash)


def b64decode(data: Union[str, bytes]) -> bytes:
    if isinstance(data, str):
        data = data.encode("utf8")
    data += b'=' * (-len(data) % 4)
    for search, replace in ((b'-', b'+'), (b'_', b'/'), (b',', b'')):
        data = data.replace(search, replace)
    return _b64decode(data)


def b64encode(data: Union[str, bytes]) -> str:
    if isinstance(data, str):
        data = data.encode("utf8")
    data = _b64encode(data).decode("utf8")
    for search, replace in (('+', '-'), ('/', '_'), ('=', '')):
        data = data.replace(search, replace)
    return data


class JWT:
    """
    Json Web Token Hmac-sha512 implementation
    """

    @staticmethod
    def decode(token: str, secret: Union[str, bytes]) -> Optional[dict]:
        if isinstance(secret, str):
            secret = b64decode(secret)

        try:
            header, payload, signature = token.split(".")
            header_dict = loads(b64decode(header).decode("utf8"))
            assert header_dict.get("alg") == "HS512"
            assert header_dict.get("typ") == "JWT"
            assert (exp := header_dict.get("exp", 0)) > time() or exp == 0
            signature = b64decode(signature)
        except (IndexError, AssertionError, ValueError):
            return

        sig = f"{header}.{payload}".encode("utf8")
        sig = new(secret, sig, sha512).digest()
        if sig == signature:
            payload = b64decode(payload).decode("utf8")
            return loads(payload)

    @staticmethod
    def encode(payload: dict, secret: Union[str, bytes], expire_timestamp: Union[int, float]=0) -> str:
        if isinstance(secret, str):
            secret = b64decode(secret)

        header = {
            "alg": "HS512",
            "typ": "JWT",
            "exp": int(expire_timestamp)
        }
        header = b64encode(dumps(header, separators=(',', ':')).encode("utf8"))
        payload = b64encode(dumps(payload, separators=(',', ':')).encode("utf8"))

        signature = f"{header}.{payload}".encode("utf8")
        signature = new(secret, signature, sha512).digest()
        signature = b64encode(signature)

        return f"{header}.{payload}.{signature}"


def c_json(json, code=200, headers=None):
    if headers is None:
        headers = {}
    if not isinstance(json, str):
        json = dumps(json)
    h = {'Content-Type': 'application/json'}
    for k, v in headers.items():
        h[k] = v
    return json, code, h


class DictList(dict):
    def __setitem__(self, key: Hashable, value: Any):
        try:
            self[key]
        except KeyError:
            super(DictList, self).__setitem__(key, [])
        self[key].append(value)