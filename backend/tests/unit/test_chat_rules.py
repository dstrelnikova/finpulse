from app.application.use_cases.chat.chat_with_llm import ChatWithLLM
from app.domain.entities.user import User


def test_truncated_model_answer_is_bad():
    answer = (
        "Давай начнем с базового плана. Для первого портфеля лучше держать часть в кэше, "
        "часть в облигациях, а потом я предложу конкретные доли п..."
    )

    assert ChatWithLLM._is_bad_response(answer)


def test_generic_assistant_intro_is_bad():
    answer = (
        "Привет! Я FinPulse, ваш финансовый ИИ-ассистент. "
        "Как я могу вам сегодня помочь? perhaps разобрать инвестиции?"
    )

    assert ChatWithLLM._is_bad_response(answer)


def test_untranslated_english_word_is_bad():
    answer = "Это позволит вам diversify риски и получить доход."

    assert ChatWithLLM._is_bad_response(answer)


def test_repeated_numbered_answer_is_bad():
    answer = """
1. Сроки: облигации имеют срок.
2. Риск: акции рискованнее.
3. Сроки: облигации имеют срок.
4. Риск: акции рискованнее.
5. Доходность: отличается.
6. Доходность: отличается.
7. Сроки погашения: облигации погашаются.
"""

    assert ChatWithLLM._is_bad_response(answer)


def test_basic_stock_bond_contradiction_is_bad():
    answer = "В облигациях владелец имеет право на получение дивидендов, а владельцы акций не имеют этих прав."

    assert ChatWithLLM._is_bad_response(answer)


def test_stock_bond_fallback_is_precise():
    answer = ChatWithLLM._fallback_response("чем отличаются облигации от акций?")

    assert "Акция - это доля в компании" in answer
    assert "Облигация - это долг эмитента" in answer
    assert "дивиденды" in answer
    assert "купонные выплаты" in answer


def test_bond_interest_fallback_is_useful():
    answer = ChatWithLLM._fallback_response("меня интересуют облигации")

    assert "Облигации - это долговые бумаги" in answer
    assert "доходность к погашению" in answer
    assert "Коротко уточните вопрос" not in answer
    assert "нестабильный вариант" not in answer


def test_generic_fallback_does_not_use_dead_end_wording():
    answer = ChatWithLLM._fallback_response("что думаешь?")

    assert "Не хочу давать неточный ответ" not in answer
    assert "нестабильный вариант" not in answer
    assert "модель" not in answer.lower()
    assert "Давайте уточним запрос" in answer


def test_investment_fallback_uses_filled_profile():
    user = User(
        id=1,
        name="Darya",
        email="darya@example.com",
        password_hash="hash",
        investment_horizon="mid",
        experience_level="intermediate",
        risk_level="medium",
        tickers=["SBER", "YDEX"],
        sectors=["banks", "it", "oil_gas"],
    )

    answer = ChatWithLLM._fallback_response("хочу инвестировать", user_profile=user)

    assert "С учетом профиля" in answer
    assert "среднесрочный" in answer
    assert "средний" in answer
    assert "SBER и YDEX" in answer
    assert "сначала зафиксируйте цель" not in answer


def test_more_clarification_fallback_asks_useful_questions():
    answer = ChatWithLLM._fallback_response("нужно больше уточнений и информации")

    assert "Ответьте на 3 вопроса" in answer
    assert "срок" in answer
    assert "просадка" in answer
    assert "нестабильный" not in answer
    assert "модель" not in answer.lower()


def test_amount_only_fallback_asks_for_goal_horizon_risk():
    answer = ChatWithLLM._fallback_response("у меня есть 50000 рублей")

    assert "срок, цель и допустимый риск" in answer
    assert "ОФЗ" in answer
    assert "10%" not in answer
    assert "5%" not in answer


def test_low_risk_amount_fallback_is_concrete():
    answer = ChatWithLLM._fallback_response("куда можно вложить 50000 рублей без сильных рисков?")

    assert "30 000-35 000 рублей" in answer
    assert "короткие ОФЗ" in answer
    assert "акции как основу" in answer


def test_reused_investment_core_is_bad_for_alternative_request():
    previous = "Предлагаю начать с 50% акций SBER и 50% облигаций YDEX."
    repeated = "Можно снова взять 50% SBER и 50% YDEX для среднего риска."

    assert ChatWithLLM._reuses_recent_investment_core(
        response_text=repeated,
        previous_answer=previous,
        last_user_message="а какие еще могут быть варианты вложений?",
    )


def test_reused_investment_core_allows_direct_followup():
    previous = "Предлагаю начать с 50% акций SBER и 50% облигаций YDEX."
    repeated = "50% SBER и 50% YDEX - это сбалансированный пример."

    assert not ChatWithLLM._reuses_recent_investment_core(
        response_text=repeated,
        previous_answer=previous,
        last_user_message="почему именно такое распределение?",
    )


def test_vague_repeat_is_bad_after_concrete_followup():
    previous = (
        "Для начала я предлагаю рассмотреть вариант инвестирования в акции. "
        "После того как вы будете более уверены, можно рассмотреть возможность инвестирования в облигации."
    )
    repeated = (
        "Для начала я предлагаю рассмотреть вариант инвестирования в акции. "
        "После того как вы будете более уверены, можно рассмотреть возможность инвестирования в облигации."
    )

    assert ChatWithLLM._reuses_vague_advice_after_concrete_followup(
        response_text=repeated,
        previous_answer=previous,
        last_user_message="а конкретно куда вкладывать?",
    )
