from __future__ import annotations

from pydantic import BaseModel, validator

from .exceptions import ValidateError


class Register(BaseModel):
    login: str
    password: str

    @validator("login", "password")
    def validate_credentials(cls: Register, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValidateError("Invalid login or/and password!")
        return value


class Login(Register):
    pass
