from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class SetActiveInput(BaseModel):
    is_active: bool


class SetSuperuserInput(BaseModel):
    is_superuser: bool
