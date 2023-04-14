from asyncio import get_event_loop

from quart import Blueprint
from quart_schema import validate_request
from sqlalchemy import select, update, or_

from src.exceptions import RequestError
from .models.users import EditProfile
from ..db import async_session
from ..gateway import Gateway
from ..models.chats import Dialog
from ..models.users import User, Session
from ..storage import S3Storage
from ..utils import getSession, c_json, getImage

users = Blueprint("users", __name__)

@users.get("/@me")
@getSession
async def get_me(session: Session):
    async with async_session() as sess:
        stmt = select(User).where(User.id == session.user_id)
        user: User = (await sess.scalars(stmt)).first()
        if user is None:
            raise RequestError("Unknown user!", 404)

    return c_json({
        "id": user.id,
        "username": user.login,
        "avatar": user.avatar
    })


async def _send_user_update(user: User):
    async with async_session() as sess:
        dialog: Dialog
        stmt = select(Dialog).where(or_(Dialog.user_1 == user.id, Dialog.user_2 == user.id)).limit(150)
        for dialog in (await sess.scalars(stmt)).all():
            await Gateway.getInstance().send_dialog_update(dialog.other_user(user.id), dialog.id, avatar=user.avatar)


@users.patch("/@me")
@validate_request(EditProfile)
@getSession
async def edit_me(data: EditProfile, session: Session):
    if data.avatar or data.avatar is None:
        async with async_session() as sess:
            stmt = select(User).where(User.id == session.user_id)
            user = (await sess.scalars(stmt)).first()

            if data.avatar is not None:
                image = getImage(data.avatar)
                if (avatar_hash := await S3Storage.getInstance().setAvatar(user.id, image, 256)) is None:
                    data.avatar = user.avatar
                else:
                    data.avatar = avatar_hash

            await sess.execute(update(User).where(User.id == user.id).values(avatar=data.avatar))
            await sess.refresh(user)
            await sess.commit()

    get_event_loop().create_task(_send_user_update(user))

    return c_json({
        "id": user.id,
        "username": user.login,
        "avatar": user.avatar
    })
