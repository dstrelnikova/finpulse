from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SetRolesIn(BaseModel):
    roles: list[str] = Field(min_length=1)


class AdminUserOut(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class PagedUsersOut(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: int
    page_size: int
