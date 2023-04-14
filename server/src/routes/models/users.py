from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, validator

from ...utils import getImage


class EditProfile(BaseModel):
    avatar: Optional[str] = ""

    @validator("avatar")
    def validate_avatar(cls: EditProfile, value: Optional[str]) -> Optional[str]:
        if value is not None:
            if not getImage(value):
                value = ""
        return value