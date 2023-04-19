from hashlib import sha256
from os import environ
from time import time

from quart import Blueprint
from quart_schema import validate_request
from simplesrp.ng_values import NG
from simplesrp.server.srp import Verifier
from sqlalchemy import select, delete

from src.exceptions import AuthError
from .models.auth import Register, Login, LoginStart
from ..db import async_session
from ..models.users import User, Session, PendingAuth
from ..utils import getSession, hashPassword, JWT, c_json, checkPassword

auth = Blueprint("auth", __name__)

@auth.post("/register")
@validate_request(Register)
async def register(data: Register):
    async with async_session() as sess:
        stmt = select(User).where(User.login == data.login)
        result = (await sess.scalars(stmt)).first()
        if result is not None:
            raise AuthError("User with this username already exists!")

        user = User(login=data.login, salt=data.salt, verifier=data.verifier, privKey=data.privKey, pubKey=data.pubKey)
        await user.create(sess)
        session = Session(user_id=user.id)
        await session.create(sess)

        await sess.commit()

    token = JWT.encode({"user_id": user.id, "session_id": session.id}, environ["SECRET_KEY"], time() + 86400 * 2)
    return c_json({"token": token})


@auth.post("/login-start")
@validate_request(LoginStart)
async def login_start(data: LoginStart):
    async with async_session() as sess:
        stmt = select(User).where(User.login == data.login)
        user: User = (await sess.scalars(stmt)).first()
        if user is None:
            raise AuthError("Invalid login or/and password!")

        srp = Verifier(user.login, bytes.fromhex(user.salt), int("0x"+user.verifier, 16), sha256, NG.NG_2048)
        salt, B = srp.getChallenge()

        pauth = PendingAuth(pubB=hex(B), privB=hex(srp.b), expire_timestamp=int(time() + 10))
        await pauth.create(sess)
        ticket = JWT.encode({"user_id": user.id, "B": B, "auth_id": pauth.id}, environ["SECRET_KEY"], time() + 10)

        await sess.commit()

    return c_json({"ticket": ticket, "salt": salt.hex(), "B": hex(B)})


@auth.post("/login")
@validate_request(Login)
async def login(data: Login):
    async with async_session() as sess:
        if not (ticket := JWT.decode(data.ticket, environ["SECRET_KEY"])):
            raise AuthError("Invalid login or/and password!")

        stmt = select(User).where(User.id == ticket["user_id"])
        user: User = (await sess.scalars(stmt)).first()
        if user is None:
            raise AuthError("Invalid login or/and password!")

        stmt = select(PendingAuth).where(PendingAuth.id == ticket["auth_id"])
        pauth: PendingAuth = (await sess.scalars(stmt)).first()
        if pauth is None:
            raise AuthError("Invalid login or/and password!")

        srp = Verifier(user.login, bytes.fromhex(user.salt), int("0x" + user.verifier, 16), sha256, NG.NG_2048)
        srp.b = int(pauth.privB, 16)
        srp.B = int(pauth.pubB, 16)
        await sess.execute(delete(PendingAuth).where(PendingAuth.id == pauth.id))
        await sess.commit()

        if not (HAMK := srp.verifyChallenge(int("0x" + data.A, 16), int("0x" + data.M, 16))):
            raise AuthError("Invalid login or/and password!")
        HAMK = int.from_bytes(HAMK, "big")

        session = Session(user_id=user.id)
        await session.create(sess)

        await sess.commit()

    token = JWT.encode({"user_id": user.id, "session_id": session.id}, environ["SECRET_KEY"], time() + 86400 * 14)
    return c_json({"token": token, "privKey": user.privKey, "H_AMK": hex(HAMK)})


@auth.post("/logout")
@getSession
async def logout(session: Session):
    async with async_session() as sess:
        await sess.execute(delete(Session).where(Session.id == session.id))
        await sess.commit()

    return "", 204