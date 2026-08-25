import pytest

from app.application.use_cases.chat.chat_with_llm import ChatModelUnavailable, ChatWithLLM
from app.infrastructure.dependencies import get_chat_use_case


class UnavailableChatUseCase:
    async def execute_async(self, **kwargs):
        del kwargs
        raise ChatModelUnavailable()


class EchoChatUseCase:
    async def execute_async(self, **kwargs):
        return kwargs["user_message"]


class SuccessfulLLM:
    async def chat_async(self, **kwargs):
        del kwargs
        return "Облигация — это долг эмитента перед инвестором с условиями возврата денег."


@pytest.mark.integration
def test_chat_returns_503_when_model_is_unavailable(client, test_app, auth_headers_for):
    test_app.dependency_overrides[get_chat_use_case] = lambda: UnavailableChatUseCase()
    try:
        response = client.post(
            "/chat/send",
            headers=auth_headers_for("user@example.com"),
            json={"message": "Что такое облигация?"},
        )
    finally:
        test_app.dependency_overrides.pop(get_chat_use_case, None)

    assert response.status_code == 503
    assert response.json()["detail"] == "CHAT_MODEL_UNAVAILABLE"


@pytest.mark.integration
@pytest.mark.parametrize("message", ["", "x" * 4001])
def test_chat_rejects_message_outside_allowed_length(client, auth_headers_for, message):
    response = client.post(
        "/chat/send",
        headers=auth_headers_for("user@example.com"),
        json={"message": message},
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_chat_accepts_message_at_max_length(client, test_app, auth_headers_for):
    test_app.dependency_overrides[get_chat_use_case] = lambda: EchoChatUseCase()
    try:
        response = client.post(
            "/chat/send",
            headers=auth_headers_for("user@example.com"),
            json={"message": "x" * 4000},
        )
    finally:
        test_app.dependency_overrides.pop(get_chat_use_case, None)

    assert response.status_code == 200
    assert response.json()["answer"] == "x" * 4000


@pytest.mark.integration
def test_chat_saves_history_and_isolates_users(
    client,
    test_app,
    auth_headers_for,
    fake_chat_message_repo,
):
    use_case = ChatWithLLM(llm=SuccessfulLLM(), chat_repo=fake_chat_message_repo)
    test_app.dependency_overrides[get_chat_use_case] = lambda: use_case
    try:
        sent = client.post(
            "/chat/send",
            headers=auth_headers_for("user@example.com"),
            json={"message": "Что такое облигация?"},
        )
        user_history = client.get(
            "/chat/history",
            headers=auth_headers_for("user@example.com"),
        )
        other_history = client.get(
            "/chat/history",
            headers=auth_headers_for("pro@example.com"),
        )
    finally:
        test_app.dependency_overrides.pop(get_chat_use_case, None)

    assert sent.status_code == 200
    assert user_history.status_code == 200
    assert [(item["role"], item["content"]) for item in user_history.json()] == [
        ("user", "Что такое облигация?"),
        ("FinPulse", "Облигация — это долг эмитента перед инвестором с условиями возврата денег."),
    ]
    assert other_history.status_code == 200
    assert other_history.json() == []
