from asyncio import CancelledError
from os import environ
from typing import Optional

from quart import Websocket
from sqlalchemy import select, and_, update

from .db import async_session
from .models.chats import Message, Dialog, ReadState
from .models.users import Session, User
from .singleton import Singleton
from .utils import DictList, JWT, newMessages


class GatewayOp:
    IDENTIFY = 0
    MESSAGE = 1
    MESSAGE_ACK = 2
    DIALOG_UPDATE = 3


class GatewayClient:
    def __init__(self, ws: Websocket):
        self.ws = ws
        self.user_id = None

    async def handle_0(self, data: dict) -> Optional[int]: # Identify
        if not (token := data.get("token")) or not (data := JWT.decode(token, environ["SECRET_KEY"])):
            return 4001
        async with async_session() as sess:
            stmt = select(Session).where(and_(Session.id == data["session_id"], Session.user_id == data["user_id"]))
            result = (await sess.scalars(stmt)).first()
            if result is None:
                return 4001
            self.user_id = result.user_id

    async def handle_2(self, data: dict) -> Optional[int]:
        if not self.user_id:
            return 4001
        async with async_session() as sess:
            if not (dialog := await Dialog.get(data["dialog_id"], self.user_id, session=sess)):
                return
            message_id = data.get("message_id", -1)
            if message_id < 0:
                stmt = select(Message).where(Message.dialog_id == data["dialog_id"]).order_by(Message.id.desc()).limit(1)
            else:
                stmt = select(Message).where(and_(Message.id == message_id, Message.dialog_id == dialog.id))
            if not (last_message := (await sess.scalars(stmt)).first()):
                return
            stmt = select(ReadState).where(and_(ReadState.user_id == self.user_id, ReadState.dialog_id == dialog.id))
            read_state = (await sess.scalars(stmt)).first()
            if read_state is None:
                read_state = ReadState(user_id=self.user_id, dialog_id=dialog.id, message_id=last_message.id)
                await read_state.create(sess)
            await sess.execute(update(ReadState).where(and_(ReadState.user_id == self.user_id, ReadState.dialog_id == dialog.id)).values(message_id=last_message.id))
            await sess.commit()

        await Gateway.getInstance().send_dialog_read_state_update(self.user_id, dialog.id)


class Gateway(Singleton):
    def __init__(self):
        self.clients = DictList()

    async def disconnect(self, client: GatewayClient, code: int) -> None:
        if client.user_id in self.clients:
            self.clients[client.user_id].remove(client)
        if code:
            await client.ws.close(code)

    async def handle_client(self, ws: Websocket) -> None:
        client = GatewayClient(ws)
        while True:
            try:
                data = await ws.receive_json()
                op_handler = getattr(client, f"handle_{data.get('op', -1)}", None)
                if op_handler is None:
                    return await self.disconnect(client, 4002) # Wrong op code
                try:
                    if res := await op_handler(data.get("d", {})):
                        return await self.disconnect(client, res)
                except:
                    return await self.disconnect(client, 4005)
                if data['op'] == GatewayOp.IDENTIFY:
                    self.clients[client.user_id] = client
            except CancelledError:
                return await self.disconnect(client, 0)

    async def send_message(self, user_id: int, dialog: Dialog, message: Message) -> None:
        for client in self.clients.get(user_id, []):
            async with async_session() as sess:
                other_user = (await sess.scalars(select(User).where(User.id == dialog.other_user(user_id)))).first()
            await client.ws.send_json({
                "op": GatewayOp.MESSAGE,
                "d": {
                    "dialog": {
                        "id": dialog.id,
                        "username": other_user.login if other_user is not None else "Unknown User",
                        "user_id": other_user.id if other_user is not None else None,
                        "avatar": other_user.avatar if other_user is not None else None,
                        "new_messages": await newMessages(user_id, dialog.id)
                    },
                    "message": {
                        "type": 1 if message.author_id != user_id else 0,
                        "text": message.text,
                        "id": message.id,
                        "time": message.created_at*1000
                    }
                }
            })

    async def send_dialog_read_state_update(self, user_id: int, dialog_id: int) -> None:
        for client in self.clients.get(user_id, []):
            await client.ws.send_json({
                "op": GatewayOp.DIALOG_UPDATE,
                "d": {
                    "id": dialog_id,
                    "new_messages": await newMessages(user_id, dialog_id)
                }
            })

    async def send_dialog_update(self, user_id: int, dialog_id: int, **data) -> None:
        if not data:
            return
        for client in self.clients.get(user_id, []):
            await client.ws.send_json({
                "op": GatewayOp.DIALOG_UPDATE,
                "d": {
                    "id": dialog_id,
                    **data
                }
            })
