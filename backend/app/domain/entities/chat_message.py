from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    id: int | None
    user_id: int
    role: str  # 'user' | 'FinPulse'
    content: str
    timestamp: datetime
    chat_id: int | None = None
