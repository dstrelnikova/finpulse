from abc import ABC, abstractmethod
import asyncio
from typing import Optional


class ILLMService(ABC):
    @abstractmethod
    def chat(self, prompt: str, user_context: Optional[dict] = None) -> str: ...

    async def chat_async(self, prompt: str, user_context: Optional[dict] = None) -> str:
        return await asyncio.to_thread(self.chat, prompt, user_context)
