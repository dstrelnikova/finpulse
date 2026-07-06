from __future__ import annotations

import asyncio
import threading
import time
import uuid
from typing import Any

import httpx
import requests

from app.application.interfaces.llm import ILLMService
from app.core.settings import settings

_GIGACHAT_REQUEST_LOCK = threading.Lock()
_GIGACHAT_LAST_REQUEST_TS = 0.0


class GigaChatLLMService(ILLMService):
    def __init__(self) -> None:
        self.auth_key = settings.GIGACHAT_AUTH_KEY.strip()
        self.scope = settings.GIGACHAT_SCOPE.strip() or "GIGACHAT_API_PERS"
        self.model = settings.GIGACHAT_MODEL.strip() or "GigaChat"
        self.oauth_url = settings.GIGACHAT_OAUTH_URL.strip()
        self.api_url = settings.GIGACHAT_API_URL.rstrip("/")
        self.timeout_sec = settings.GIGACHAT_TIMEOUT_SEC
        self.verify_ssl = settings.GIGACHAT_VERIFY_SSL
        self.min_request_interval_sec = settings.GIGACHAT_MIN_REQUEST_INTERVAL_SEC
        self.max_retries = settings.GIGACHAT_MAX_RETRIES
        self._token: str | None = None
        self._expires_at: float = 0
        self._token_lock = threading.Lock()
        self._async_token_lock = asyncio.Lock()

    def _token_valid(self) -> bool:
        return bool(self._token) and time.time() < self._expires_at - 60

    def _get_token(self) -> str:
        if self._token_valid():
            return str(self._token)
        with self._token_lock:
            if self._token_valid():
                return str(self._token)
            self._refresh_token()
            return str(self._token)

    def _refresh_token(self) -> None:
        if not self.auth_key:
            raise RuntimeError("GigaChat auth key is empty")

        response = requests.post(
            self.oauth_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": str(uuid.uuid4()),
                "Authorization": self._authorization_header(),
            },
            data={"scope": self.scope},
            timeout=self.timeout_sec,
            verify=self.verify_ssl,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"GigaChat OAuth HTTP {response.status_code}: {response.text[:500]}")

        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise RuntimeError("GigaChat OAuth response does not contain access_token")

        self._token = str(access_token)
        expires_at = data.get("expires_at")
        self._expires_at = self._normalize_expires_at(expires_at)

    async def _get_token_async(self) -> str:
        if self._token_valid():
            return str(self._token)
        async with self._async_token_lock:
            if self._token_valid():
                return str(self._token)
            await self._refresh_token_async()
            return str(self._token)

    async def _refresh_token_async(self) -> None:
        if not self.auth_key:
            raise RuntimeError("GigaChat auth key is empty")

        async with httpx.AsyncClient(timeout=self.timeout_sec, verify=self.verify_ssl) as client:
            response = await client.post(
                self.oauth_url,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "RqUID": str(uuid.uuid4()),
                    "Authorization": self._authorization_header(),
                },
                data={"scope": self.scope},
            )

        if response.status_code >= 400:
            raise RuntimeError(f"GigaChat OAuth HTTP {response.status_code}: {response.text[:500]}")

        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise RuntimeError("GigaChat OAuth response does not contain access_token")

        self._token = str(access_token)
        self._expires_at = self._normalize_expires_at(data.get("expires_at"))

    @staticmethod
    def _normalize_expires_at(value: Any) -> float:
        now = time.time()
        try:
            expires_at = float(value)
        except (TypeError, ValueError):
            return now + 30 * 60

        if expires_at > 10_000_000_000:
            expires_at = expires_at / 1000
        if expires_at < now:
            expires_at = now + 30 * 60
        return expires_at

    def _authorization_header(self) -> str:
        if self.auth_key.lower().startswith("basic "):
            return self.auth_key
        return f"Basic {self.auth_key}"

    def _payload(self, prompt: str, user_context: dict | None) -> dict:
        is_chat_request = bool(user_context and "chat_id" in user_context)
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.15 if is_chat_request else 0.05,
            "top_p": 0.85,
            "max_tokens": settings.GIGACHAT_CHAT_MAX_TOKENS if is_chat_request else settings.GIGACHAT_NEWS_MAX_TOKENS,
            "stream": False,
        }

    def _wait_for_rate_limit(self) -> None:
        global _GIGACHAT_LAST_REQUEST_TS

        if self.min_request_interval_sec <= 0:
            return
        with _GIGACHAT_REQUEST_LOCK:
            now = time.monotonic()
            wait_sec = self.min_request_interval_sec - (now - _GIGACHAT_LAST_REQUEST_TS)
            if wait_sec > 0:
                time.sleep(wait_sec)
            _GIGACHAT_LAST_REQUEST_TS = time.monotonic()

    @staticmethod
    def _response_text(data: dict) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("GigaChat response does not contain choices")
        message = choices[0].get("message") or {}
        return str(message.get("content") or "").strip()

    def chat(self, prompt: str, user_context: dict | None = None) -> str:
        token = self._get_token()
        response = None
        for attempt in range(self.max_retries + 1):
            self._wait_for_rate_limit()
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                json=self._payload(prompt, user_context),
                timeout=self.timeout_sec,
                verify=self.verify_ssl,
            )
            if response.status_code != 429 or attempt >= self.max_retries:
                break
            retry_after = response.headers.get("Retry-After")
            try:
                wait_sec = float(retry_after) if retry_after else self.min_request_interval_sec * (attempt + 2)
            except ValueError:
                wait_sec = self.min_request_interval_sec * (attempt + 2)
            time.sleep(max(1.0, wait_sec))

        if response is None:
            raise RuntimeError("GigaChat request was not sent")
        if response.status_code >= 400:
            raise RuntimeError(f"GigaChat HTTP {response.status_code}: {response.text[:500]}")
        return self._response_text(response.json())

    async def chat_async(self, prompt: str, user_context: dict | None = None) -> str:
        token = await self._get_token_async()
        async with httpx.AsyncClient(timeout=self.timeout_sec, verify=self.verify_ssl) as client:
            response = await client.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                json=self._payload(prompt, user_context),
            )

        if response.status_code >= 400:
            raise RuntimeError(f"GigaChat HTTP {response.status_code}: {response.text[:500]}")
        return self._response_text(response.json())
