from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    message: str
    chat_id: Optional[int] = None


class ChatOut(BaseModel):
    answer: str
    chat_id: int


class ChatMessageOut(BaseModel):
    id: int
    role: str  # "user" / "assistant"
    content: str
    created_at: datetime


class ChatCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    topic: Optional[str] = Field(default=None, max_length=120)


class ChatSessionOut(BaseModel):
    id: int
    title: str
    topic: Optional[str]
    is_default: bool
