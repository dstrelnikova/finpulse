from datetime import datetime

from app.application.use_cases.chat.build_prompt import build_chat_context
from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.user import User


def test_chat_prompt_includes_profile_context():
    user = User(
        id=1,
        name="Darya",
        email="darya@example.com",
        password_hash="hash",
        investment_horizon="mid",
        experience_level="intermediate",
        risk_level="medium",
        tickers=["SBER", "YDEX"],
        sectors=["banks", "it"],
    )
    messages = [
        ChatMessage(
            id=1,
            user_id=1,
            chat_id=1,
            role="user",
            content="Что думаешь про мой профиль?",
            timestamp=datetime.utcnow(),
        )
    ]

    prompt = build_chat_context(messages, user_profile=user)

    assert "Профиль пользователя:" in prompt
    assert "среднесрочный, месяцы" in prompt
    assert "опытный, можно давать больше деталей" in prompt
    assert "средний, сбалансированный профиль" in prompt
    assert "SBER, YDEX" in prompt
    assert "банки, IT" in prompt
    assert "Профиль пользователя заполнен: да" in prompt
    assert "Профиль пользователя - обязательный контекст" in prompt
    assert "не отвечай универсально" in prompt


def test_chat_prompt_warns_against_repeating_previous_options():
    messages = [
        ChatMessage(
            id=1,
            user_id=1,
            chat_id=1,
            role="user",
            content="куда вложить 50000 рублей?",
            timestamp=datetime.utcnow(),
        ),
        ChatMessage(
            id=2,
            user_id=1,
            chat_id=1,
            role="FinPulse",
            content="Можно рассмотреть 50% SBER и 50% YDEX.",
            timestamp=datetime.utcnow(),
        ),
        ChatMessage(
            id=3,
            user_id=1,
            chat_id=1,
            role="user",
            content="а какие еще могут быть варианты вложений?",
            timestamp=datetime.utcnow(),
        ),
    ]

    prompt = build_chat_context(messages)

    assert "Пользователь просит дополнительные или другие варианты" in prompt
    assert "Недавний ответ, который нельзя пересказывать" in prompt
    assert "50% SBER и 50% YDEX" in prompt


def test_chat_prompt_answers_broad_but_clear_financial_topic():
    messages = [
        ChatMessage(
            id=1,
            user_id=1,
            chat_id=1,
            role="user",
            content="меня интересуют облигации",
            timestamp=datetime.utcnow(),
        )
    ]

    prompt = build_chat_context(messages)

    assert "широкий, но понятный финансовый запрос" in prompt
    assert "интересуют облигации" in prompt
