from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.user import User

MAX_PROMPT_CHARS = 2400
MAX_HISTORY_MESSAGES = 8
MAX_MESSAGE_CHARS = 500

HORIZON_LABELS = {
    "short": "краткосрочный, дни-недели",
    "mid": "среднесрочный, месяцы",
    "long": "долгосрочный, годы",
}

EXPERIENCE_LABELS = {
    "beginner": "новичок, объяснять проще",
    "intermediate": "опытный, можно давать больше деталей",
    "pro": "профессионал, можно использовать рыночную терминологию",
}

RISK_LABELS = {
    "low": "низкий, осторожный профиль",
    "medium": "средний, сбалансированный профиль",
    "high": "высокий, допускает повышенную волатильность",
}

SECTOR_LABELS = {
    "banks": "банки",
    "oil_gas": "нефть и газ",
    "metals_mining": "металлы и добыча",
    "it": "IT",
    "consumer": "потребительский сектор",
    "telecom": "телеком",
    "utilities": "электроэнергетика",
    "real_estate": "недвижимость",
    "transport": "транспорт",
    "industrials": "промышленность",
    "financials_other": "финансы, прочее",
}


def _compact(text: str, max_chars: int = MAX_MESSAGE_CHARS) -> str:
    text = " ".join((text or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _profile_context(user: User | None) -> str:
    if not user:
        return "Профиль не передан."

    lines = [
        f"- рынок: {user.market or 'не указан'}",
        f"- горизонт: {HORIZON_LABELS.get(user.investment_horizon or '', user.investment_horizon or 'не указан')}",
        f"- опыт: {EXPERIENCE_LABELS.get(user.experience_level or '', user.experience_level or 'не указан')}",
        f"- риск: {RISK_LABELS.get(user.risk_level or '', user.risk_level or 'не указан')}",
        f"- интересующие тикеры: {', '.join(user.tickers[:8]) if user.tickers else 'не указаны'}",
        "- интересующие сектора: "
        + (", ".join(SECTOR_LABELS.get(s, s) for s in user.sectors[:8]) if user.sectors else "не указаны"),
    ]
    return "\n".join(lines)


def _has_filled_profile(user: User | None) -> bool:
    if not user:
        return False
    return any(
        [
            user.investment_horizon,
            user.experience_level,
            user.risk_level,
            user.tickers,
            user.sectors,
        ]
    )


def _asks_for_more_options(text: str) -> bool:
    normalized = (text or "").lower()
    option_markers = ("вариант", "альтернатив", "способ", "инструмент", "актив")
    more_markers = ("еще", "ещё", "друг", "кроме", "без повтор", "не повтор")
    has_options = any(marker in normalized for marker in option_markers)
    asks_more = any(marker in normalized for marker in more_markers)
    return has_options and asks_more


def _last_assistant_message(messages: list[ChatMessage]) -> str:
    return next((msg.content for msg in reversed(messages) if msg.role == "FinPulse"), "")


def build_chat_context(messages: list[ChatMessage], user_profile: User | None = None) -> str:
    """
    Собирает контекст для модели из последних сообщений,
    обрезая по длине (по символам).
    """
    if not messages:
        last_user_message = ""
        context_messages: list[ChatMessage] = []
    else:
        last_user_idx = next((idx for idx in range(len(messages) - 1, -1, -1) if messages[idx].role == "user"), -1)
        last_user_message = messages[last_user_idx].content if last_user_idx >= 0 else messages[-1].content
        context_messages = messages[:last_user_idx] if last_user_idx >= 0 else messages[:-1]

    parts: list[str] = []
    total_len = 0

    recent_messages = context_messages[-MAX_HISTORY_MESSAGES:]

    for msg in reversed(recent_messages):
        role = "Пользователь" if msg.role == "user" else "FinPulse"
        chunk = f"{role}: {_compact(msg.content)}\n"
        chunk_len = len(chunk)

        if total_len + chunk_len > MAX_PROMPT_CHARS:
            break

        parts.append(chunk)
        total_len += chunk_len

    parts = list(reversed(parts))

    history_text = "".join(parts).strip() or "Нет предыдущего контекста."
    last_user_text = _compact(last_user_message, max_chars=900)
    previous_answer = _compact(_last_assistant_message(context_messages), max_chars=700)
    anti_repeat_text = ""
    if _asks_for_more_options(last_user_message) and previous_answer:
        anti_repeat_text = (
            "Пользователь просит дополнительные или другие варианты. Не повторяй основные тикеры, "
            "инструменты, проценты и выводы из недавнего ответа; сначала расширь набор альтернатив.\n"
            f"Недавний ответ, который нельзя пересказывать:\n{previous_answer}\n\n"
        )

    system_prompt = (
        "Ты - FinPulse, финансовый помощник внутри чата.\n"
        "Отвечай строго на блок «Последнее сообщение пользователя» ниже. История нужна только как фон.\n"
        "Пиши по-русски, конкретно и без шаблонных приветствий.\n"
        "Запрещено начинать с самопрезентации вроде «Я FinPulse», «Я финансовый ИИ-ассистент», "
        "«Как я могу помочь» или перечисления возможностей сервиса.\n"
        "Не смешивай русский с английским, китайским, японским или корейским. "
        "Не используй иероглифы, транслит и отдельные английские слова вроде diversify или perhaps. "
        "Исключение: биржевые тикеры вроде SBER, MOEX, LKOH и общеупотребимые секторные обозначения вроде IT.\n"
        "Не добавляй роль, префикс «FinPulse:» или подпись автора.\n"
        "Профиль пользователя - обязательный контекст для любых вопросов про инвестиции, портфель, риск, "
        "акции, облигации, тикеры, сектора или фразы вроде «хочу инвестировать». "
        "Если профиль заполнен, не отвечай универсально «сначала выберите горизонт и риск»: эти данные уже есть. "
        "Сразу используй известные значения профиля в логике ответа.\n"
        "Если профиль заполнен и вопрос инвестиционный, в первом предложении коротко отрази персонализацию: "
        "например «С учетом среднего риска и среднесрочного горизонта...». "
        "Не пересказывай профиль целиком и не перечисляй все поля без нужды.\n"
        "Если профиль противоречит сообщению пользователя, приоритет у последнего сообщения пользователя.\n"
        "Если в профиле есть тикеры или сектора, используй их как контекст интересов, а не как рекомендацию купить.\n"
        "Не зацикливайся на тикерах из профиля: если пользователь просит варианты, показывай разные классы активов "
        "и сценарии риска, а не только интересующие тикеры.\n"
        "Если пользователь просит «еще», «другие варианты» или альтернативы, не повторяй прошлую рекомендацию "
        "с теми же активами и долями; дай новые категории или новые примеры.\n"
        "Если пользователь уже назвал сумму, срок или цель, используй эти данные и не проси повторить их.\n"
        "Если пользователь назвал только сумму без цели, срока и риска, не придумывай проценты и инструменты. "
        "Коротко спроси про цель, горизонт и допустимую просадку, добавив один осторожный пример направления.\n"
        "Если пользователь просит больше уточнений или информации, задай 2-3 конкретных вопроса по текущей теме "
        "и объясни, зачем они нужны. Не отвечай аварийными фразами про нестабильный ответ.\n"
        "Если пользователь спрашивает «конкретно куда?», «куда именно вложить?» или похожий follow-up, "
        "не повторяй прошлое общее объяснение. Дай прикладную структуру: классы инструментов, примерные доли "
        "или диапазоны сумм и 2-3 критерия проверки. Для низкого риска не начинай с акций как основной идеи.\n"
        "Если пользователь обозначил широкую тему вроде «интересуют облигации», «хочу про акции» "
        "или «расскажи про риск», дай короткий вводный обзор по теме и предложи 2-3 следующих шага. "
        "Не проси уточнить широкий, но понятный финансовый запрос.\n"
        "Если не хватает только риска, предложи осторожный базовый вариант и спроси про риск в конце одним вопросом.\n"
        "Если вопрос простой, ответь одной короткой фразой.\n"
        "Для финансовых тем: не давай прямых команд купить/продать; объясняй риски, сценарии и проверяемые шаги.\n"
        "Для образовательных вопросов вроде «чем отличается X от Y» дай короткое сравнение без советов.\n"
        "Базовые правила: акция - доля в компании и возможные дивиденды; облигация - долг эмитента, "
        "купоны и погашение. "
        "Акционер может иметь право голоса; владелец облигации обычно не участвует в управлении компанией.\n"
        "Не повторяй один и тот же пункт другими словами. Не делай больше 5 пунктов.\n"
        "Формат: 1-2 коротких абзаца или до 5 пунктов. Заверши мысль полностью.\n\n"
        f"Профиль пользователя заполнен: {'да' if _has_filled_profile(user_profile) else 'нет'}.\n"
        f"Профиль пользователя:\n{_profile_context(user_profile)}\n\n"
        f"{anti_repeat_text}"
        "История до последнего сообщения:\n"
    )

    return (
        f"{system_prompt}{history_text}\n\n"
        f"Последнее сообщение пользователя:\n{last_user_text}\n\n"
        "Ответ:"
    )
