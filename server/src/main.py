from asyncio import CancelledError
from os import environ

from quart import Quart, Response, websocket
from quart_schema import QuartSchema, RequestSchemaValidationError

from .db import init_db
from .exceptions import RequestError
from .gateway import Gateway
from .routes import auth, chat, users
from .storage import S3Storage
from .utils import c_json

app = Quart("IdkChat")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite+aiosqlite:///idkchat.db"
gw = Gateway()
storage = S3Storage(environ["S3_GATEWAY"], environ["S3_ID"], environ["S3_KEY"], environ["S3_BUCKET"])

QuartSchema(app)


@app.before_serving
async def _init_db():
    await init_db()


@app.errorhandler(RequestError)
async def handle_idkchat_validation_error(error: RequestError):
    return c_json({"message": error.message}, error.code)


@app.errorhandler(RequestSchemaValidationError)
async def handle_validation_error(error: RequestSchemaValidationError):
    for error in error.validation_error.errors():
        loc = error["loc"][0]
        if error["type"] == "value_error.missing":
            return c_json({"message": f"Required field: {loc}."}, 400)
        elif error["type"] in ("type_error.integer", "type_error.float"):
            message = "Value is not int" if error["type"] == "type_error.integer" else "Value is not float"
            return c_json({"message": f"{message}: {loc}."}, 400)
        else:
            return c_json({"message": f"Something wrong with this value: {loc}."}, 400)
    return c_json({"message": "Something wrong with data you provided!"}, 400)


@app.after_request
async def set_cors_headers(response: Response) -> Response:
    response.headers['Server'] = "YEPcord"
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['Access-Control-Allow-Headers'] = "*"
    response.headers['Access-Control-Allow-Methods'] = "*"
    response.headers['Content-Security-Policy'] = "connect-src *;"
    return response


app.register_blueprint(auth.auth, url_prefix="/api/v1/auth")
app.register_blueprint(chat.chat, url_prefix="/api/v1/chat")
app.register_blueprint(users.users, url_prefix="/api/v1/users")


@app.websocket("/ws")
async def websocket_gateway():
    ws = websocket._get_current_object()
    await gw.handle_client(ws)
