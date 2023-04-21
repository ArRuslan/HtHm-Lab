from __future__ import annotations

from base64 import b64decode
from typing import Optional

from pydantic import BaseModel, validator

from src.exceptions import ValidateError


class MessagesGet(BaseModel):
    dialog_id: Optional[int]

    @validator("dialog_id")
    def validate_dialog_id(cls: MessagePost, value: int) -> int:
        if value is None:
            raise ValidateError("Unknown dialog!")
        return value


class MessagePost(BaseModel):
    dialog_id: int
    text: str

    @validator("text")
    def validate_text(cls: MessagePost, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValidateError("Message is empty!")
        try:
            raw = b64decode(value.encode("utf8"))
            assert len(raw) <= 2048
            assert raw % 256 == 0
        except:
            raise ValidateError("Invalid message!")
        return value


class DialogCreate(BaseModel):
    username: str

    @validator("username")
    def validate_credentials(cls: DialogCreate, value: str) -> str:
        value = value.strip()
        if value.startswith("@"): value = value[1:]
        if not value:
            raise ValidateError("Invalid username!")
        return value