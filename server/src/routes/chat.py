from random import shuffle
from time import time

from quart import Blueprint
from quart_schema import validate_querystring, validate_request
from sqlalchemy import select, and_, or_

from .models.chat import MessagesGet, MessagePost, DialogCreate
from ..db import async_session
from ..exceptions import ValidateError
from ..gateway import Gateway
from ..models.chats import Dialog, Message
from ..models.users import Session, User
from ..utils import getSession, c_json, getDialog, newMessages

chat = Blueprint("chat", __name__)


@chat.get("/dialogs")
@getSession
async def get_dialogs(session: Session):
    dialogs = []
    async with async_session() as sess:
        stmt = select(Dialog).where(and_(
            or_(Dialog.user_1 == session.user_id, Dialog.user_2 == session.user_id)
        ))
        for dialog in await sess.scalars(stmt):
            other_user = (await sess.scalars(select(User).where(User.id == dialog.other_user(session.user_id)))).first()
            dialogs.append({
                "id": dialog.id,
                "username": other_user.login if other_user is not None else "Unknown User",
                "new_messages": await newMessages(session.user_id, dialog.id),
                "user_id": other_user.id if other_user is not None else None,
                "avatar": other_user.avatar if other_user is not None else None,
            })
    return c_json(dialogs)


@chat.post("/dialogs")
@validate_request(DialogCreate)
@getSession
async def create_dialog(session: Session, data: DialogCreate):
    async with async_session() as sess:
        stmt = select(User).where(User.login == data.username)
        other_user = (await sess.scalars(stmt)).first()
        if other_user is None:
            raise ValidateError("No users with this username exists!")

        stmt = select(Dialog).where(or_(
            and_(Dialog.user_1 == session.user_id, Dialog.user_2 == other_user.id),
            and_(Dialog.user_1 == other_user.id, Dialog.user_2 == session.user_id)
        ))
        dialog = (await sess.scalars(stmt)).first()
        if dialog is not None:
            return c_json({
                "id": dialog.id,
                "username": other_user.login,
                "user_id": other_user.id if other_user is not None else None,
                "avatar": other_user.avatar
            })

        dialog = Dialog(user_1=session.user_id, user_2=other_user.id)
        await dialog.create(sess)

        message = Message(dialog_id=dialog.id, author_id=session.user_id, text="Dialog started!", created_at=int(time()))
        await message.create(sess)

        await sess.commit()

    await Gateway.getInstance().send_message(session.user_id, dialog, message)
    await Gateway.getInstance().send_message(dialog.other_user(session.user_id), dialog, message)

    return c_json({
        "id": dialog.id,
        "username": other_user.login,
        "avatar": other_user.avatar
    })


@chat.get("/messages")
@validate_querystring(MessagesGet)
@getSession
@getDialog
async def get_messages(query_args: MessagesGet, dialog: Dialog, session: Session):
    messages = []

    async with async_session() as sess:
        stmt = select(Message).where(Message.dialog_id == dialog.id)
        for message in (await sess.scalars(stmt)).all():
            messages.append({
                "type": 1 if message.author_id != session.user_id else 0,
                "text": message.text,
                "id": message.id,
                "time": message.created_at*1000
            })

    return c_json(messages)


@chat.post("/messages")
@validate_request(MessagePost)
@getSession
@getDialog
async def post_message(data: MessagePost, dialog: Dialog, session: Session):
    async with async_session() as sess:
        message = Message(dialog_id=dialog.id, author_id=session.user_id, text=data.text, created_at=int(time()))
        await message.create(sess)

        await sess.commit()

    await Gateway.getInstance().send_message(session.user_id, dialog, message)
    await Gateway.getInstance().send_message(dialog.other_user(session.user_id), dialog, message)

    return "", 204
