from __future__ import annotations

import re

from pydantic import BaseModel, validator

from ...exceptions import ValidateError


class Register(BaseModel):
    login: str
    password: str

    @validator("login")
    def validate_login(cls: Register, value: str) -> str:
        value = value.strip()
        value = re.sub('[\W_]+', '', value)
        if not value:
            raise ValidateError("Invalid login!")
        if len(value) < 5:
            raise ValidateError("Username length must be 5 or greater!")
        return value

    @validator("password")
    def validate_password(cls: Register, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValidateError("Invalid password!")
        if len(value) < 8:
            raise ValidateError("Password length must be 8 or greater!")
        return value


class Login(Register):
    pass
