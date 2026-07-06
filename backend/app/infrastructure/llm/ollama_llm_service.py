import asyncio
import threading

import httpx
import requests

from app.application.interfaces.llm import ILLMService
from app.core.settings import settings

_OLLAMA_MAX_CONCURRENCY = int(getattr(settings, "OLLAMA_MAX_CONCURRENCY", 1))
_OLLAMA_SEMAPHORE = threading.BoundedSemaphore(_OLLAMA_MAX_CONCURRENCY)
_OLLAMA_ASYNC_SEMAPHORE = asyncio.BoundedSemaphore(_OLLAMA_MAX_CONCURRENCY)
_OLLAMA_ASYNC_LIMITS = httpx.Limits(
    max_connections=_OLLAMA_MAX_CONCURRENCY,
    max_keepalive_connections=_OLLAMA_MAX_CONCURRENCY,
)


class OllamaLLMService(ILLMService):
    def __init__(self) -> None:
        self.model = settings.OLLAMA_MODEL
        base = settings.OLLAMA_URL.rstrip("/")
        self.url = f"{base}/api/generate"

    def _payload(self, prompt: str) -> dict:
        return {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.75,
                "repeat_penalty": 1.12,
                "num_predict": settings.OLLAMA_CHAT_NUM_PREDICT,
                "num_ctx": 3072,
            },
            "keep_alive": "10m",
        }

    def chat(self, prompt: str, user_context: dict | None = None) -> str:
        acquired = _OLLAMA_SEMAPHORE.acquire(blocking=False)
        if not acquired:
            raise RuntimeError("Ollama busy: too many concurrent chat requests")

        try:
            try:
                response = requests.post(
                    self.url,
                    json=self._payload(prompt),
                    timeout=settings.OLLAMA_CHAT_TIMEOUT_SEC,
                )
            except requests.RequestException as exc:
                raise RuntimeError(f"Ollama unreachable: {exc}") from exc

            if response.status_code >= 400:
                raise RuntimeError(f"Ollama HTTP {response.status_code}: {response.text[:500]}")

            data = response.json()
            if data.get("done") is False:
                raise RuntimeError("Ollama response was not completed")
            return str(data.get("response") or "").strip()
        finally:
            _OLLAMA_SEMAPHORE.release()

    async def chat_async(self, prompt: str, user_context: dict | None = None) -> str:
        async with _OLLAMA_ASYNC_SEMAPHORE:
            try:
                async with httpx.AsyncClient(
                    timeout=settings.OLLAMA_CHAT_TIMEOUT_SEC,
                    limits=_OLLAMA_ASYNC_LIMITS,
                ) as client:
                    response = await client.post(self.url, json=self._payload(prompt))
            except httpx.HTTPError as exc:
                raise RuntimeError(f"Ollama unreachable: {exc}") from exc

            if response.status_code >= 400:
                raise RuntimeError(f"Ollama HTTP {response.status_code}: {response.text[:500]}")

            data = response.json()
            if data.get("done") is False:
                raise RuntimeError("Ollama response was not completed")
            return str(data.get("response") or "").strip()
