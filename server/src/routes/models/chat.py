from __future__ import annotations

from pydantic import BaseModel, validator

from src.routes.models.exceptions import ValidateError


class MessagesGet(BaseModel):
    dialog_id: str


class MessagePost(BaseModel):
    dialog_id: str
    text: str

    @validator("text")
    def validate_text(cls: MessagePost, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValidateError("Message is empty!")
        return value[:1024]
