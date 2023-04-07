from quart import Quart
from quart_schema import QuartSchema

from .routes import auth, chat

app = Quart("IdkChat")
QuartSchema(app)

app.register_blueprint(auth.auth, url_prefix="/api/v1/auth")
app.register_blueprint(chat.chat, url_prefix="/api/v1/chat")
