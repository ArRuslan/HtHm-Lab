from os import environ
from time import time

from quart import Blueprint
from quart_schema import validate_request
from sqlalchemy import select, delete

from src.exceptions import AuthError
from .models.auth import Register, Login
from ..db import async_session
from ..models.users import User, Session
from ..utils import getSession, hashPassword, JWT, c_json, checkPassword

auth = Blueprint("auth", __name__)

@auth.post("/register")
@validate_request(Register)
async def register(data: Register):
    password = hashPassword(data.password)
    async with async_session() as sess:
        stmt = select(User).where(User.login == data.login)
        result = (await sess.scalars(stmt)).first()
        if result is not None:
            raise AuthError("User with this username already exists!")

        user = User(login=data.login, password=password)
        await user.create(sess)
        session = Session(user_id=user.id)
        await session.create(sess)

        await sess.commit()

    token = JWT.encode({"user_id": user.id, "session_id": session.id}, environ["SECRET_KEY"], time() + 86400 * 14)
    return c_json({"token": token})

@auth.post("/login")
@validate_request(Login)
async def login(data: Login):
    async with async_session() as sess:
        stmt = select(User).where(User.login == data.login)
        result = (await sess.scalars(stmt)).first()
        if result is None:
            raise AuthError("Invalid login or/and password!")

        if not checkPassword(data.password, result.password):
            raise AuthError("Invalid login or/and password!")

        session = Session(user_id=result.id)
        await session.create(sess)
        await sess.commit()

    token = JWT.encode({"user_id": result.id, "session_id": session.id}, environ["SECRET_KEY"], time() + 86400 * 14)
    return c_json({"token": token})


@auth.post("/logout")
@getSession
async def logout(session: Session):
    async with async_session() as sess:
        await sess.execute(delete(Session).where(Session.id == session.id))
        await sess.commit()

    return "", 204