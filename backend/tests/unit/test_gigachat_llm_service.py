from app.core.settings import settings
from app.infrastructure.llm.gigachat_llm_service import GigaChatLLMService


class _Response:
    def __init__(self, payload: dict, status_code: int = 200, text: str = ""):
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._payload


def test_gigachat_service_gets_token_and_sends_chat(monkeypatch):
    monkeypatch.setattr(settings, "GIGACHAT_AUTH_KEY", "test-auth-key")
    monkeypatch.setattr(settings, "GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    monkeypatch.setattr(settings, "GIGACHAT_MODEL", "GigaChat")
    monkeypatch.setattr(settings, "GIGACHAT_OAUTH_URL", "https://oauth.example.test")
    monkeypatch.setattr(settings, "GIGACHAT_API_URL", "https://api.example.test/v1")
    monkeypatch.setattr(settings, "GIGACHAT_VERIFY_SSL", True)

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        if url == "https://oauth.example.test":
            return _Response({"access_token": "token", "expires_at": 4_102_444_800})
        return _Response({"choices": [{"message": {"content": "{\"ok\": true}"}}]})

    monkeypatch.setattr("app.infrastructure.llm.gigachat_llm_service.requests.post", fake_post)

    service = GigaChatLLMService()

    assert service.chat("ping") == "{\"ok\": true}"
    assert calls[0][1]["headers"]["Authorization"] == "Basic test-auth-key"
    assert calls[0][1]["data"] == {"scope": "GIGACHAT_API_PERS"}
    assert calls[1][0] == "https://api.example.test/v1/chat/completions"
    assert calls[1][1]["headers"]["Authorization"] == "Bearer token"
    assert calls[1][1]["json"]["model"] == "GigaChat"
