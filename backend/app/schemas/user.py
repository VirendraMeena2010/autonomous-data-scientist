from __future__ import annotations

from pydantic import BaseModel, ConfigDict,EmailStr,Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    storage_quota_bytes: int
    storage_used_bytes: int

class SignupInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=200)


class LoginInput(BaseModel):
    email: EmailStr
    password: str