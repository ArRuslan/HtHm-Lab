from __future__ import annotations

import re

from pydantic import BaseModel, validator

from ...exceptions import ValidateError


class Register(BaseModel):
    login: str
    salt: str
    verifier: str
    privKey: str
    pubKey: str

    @validator("login")
    def validate_login(cls: Register, value: str) -> str:
        value = value.strip()
        value = re.sub('[\W_]+', '', value)
        if not value:
            raise ValidateError("Invalid login!")
        if len(value) < 5:
            raise ValidateError("Username length must be 5 or greater!")
        return value


class LoginStart(BaseModel):
    login: str

class Login(BaseModel):
    A: str
    M: str
    ticket: str
