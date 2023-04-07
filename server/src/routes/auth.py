from quart import Blueprint
from quart_schema import validate_request

from .models.auth import Register, Login
from ..utils import getSession

auth = Blueprint("auth", __name__)

@auth.post("/register")
@validate_request(Register)
async def register(data: Register):
    return "", 501

@auth.post("/login")
@validate_request(Login)
async def register(data: Login):
    return "", 501


@auth.post("/logout")
@getSession
async def logout(session):
    return "", 501