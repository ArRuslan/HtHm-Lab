from asyncio import CancelledError
from os import environ
from typing import Optional

from quart import Websocket
from sqlalchemy import select, and_

from .db import async_session
from .models.chats import Message, Dialog
from .models.users import Session, User
from .singleton import Singleton
from .utils import DictList, JWT


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
                if res := await op_handler(data.get("d", {})):
                    return await self.disconnect(client, res)
                if data['op'] == 0:
                    self.clients[client.user_id] = client
            except CancelledError:
                return await self.disconnect(client, 0)

    async def send_message(self, user_id: int, dialog: Dialog, message: Message) -> None:
        for client in self.clients.get(user_id):
            async with async_session() as sess:
                other_user = (await sess.scalars(select(User).where(User.id == dialog.other_user(user_id)))).first()
            await client.ws.send_json({
                "op": 1,
                "d": {
                    "dialog": {
                        "id": dialog.id,
                        "username": other_user.login if other_user is not None else "Unknown User"
                    },
                    "message": {
                        "type": 1 if message.author_id != user_id else 0,
                        "text": message.text,
                        "id": message.id,
                        "time": message.created_at*1000
                    }
                }
            })