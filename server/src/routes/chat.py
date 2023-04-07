from quart import Blueprint
from quart_schema import validate_querystring, validate_request

from .models.chat import MessagesGet, MessagePost
from ..models.users import Session
from ..utils import getSession

chat = Blueprint("chat", __name__)


@chat.get("/dialogs")
@getSession
async def get_dialogs(session: Session):
    return "", 501


@chat.get("/messages")
@validate_querystring(MessagesGet)
@getSession
async def get_dialogs(query_args: MessagesGet, session: Session):
    return "", 501


@chat.post("/messages")
@validate_request(MessagePost)
@getSession
async def get_dialogs(data: MessagePost, session: Session):
    return "", 501
