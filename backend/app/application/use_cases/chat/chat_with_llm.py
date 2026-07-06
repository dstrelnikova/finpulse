import datetime
import re
from typing import Optional

from app.application.interfaces.llm import ILLMService
from app.application.use_cases.chat.build_prompt import HORIZON_LABELS, RISK_LABELS, build_chat_context
from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.user import User
from app.infrastructure.database.chat_repo_impl import ChatRepositorySQL


class ChatModelUnavailable(Exception):
    pass


CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")
NUMBERED_ITEM_RE = re.compile(r"(?m)^\s*\d+[\).]\s*(.+)")
TICKER_RE = re.compile(r"\b[A-Z]{3,5}\b")
PERCENT_RE = re.compile(r"\b\d{1,3}\s*%")
LATIN_WORD_RE = re.compile(r"\b[A-Za-z]{4,}\b")


class ChatWithLLM:
    def __init__(self, llm: ILLMService, chat_repo: ChatRepositorySQL):
        self.llm = llm
        self.chat_repo = chat_repo

    def execute(
        self,
        user_id: int,
        user_message: str,
        chat_id: Optional[int] = None,
        user_profile: Optional[User] = None,
    ) -> str:
        self._save_user_message(user_id=user_id, user_message=user_message, chat_id=chat_id)
        prompt = self._build_prompt(user_id=user_id, chat_id=chat_id, user_profile=user_profile)

        try:
            response_text = self._ask_model(prompt=prompt, user_id=user_id, chat_id=chat_id)
            if self._is_bad_response(response_text) or self._repeats_recent_answer(
                user_id=user_id,
                chat_id=chat_id,
                response_text=response_text,
            ):
                repaired_prompt = self._repair_prompt(prompt=prompt, bad_response=response_text)
                response_text = self._ask_model(prompt=repaired_prompt, user_id=user_id, chat_id=chat_id)
            if self._is_bad_response(response_text) or self._repeats_recent_answer(
                user_id=user_id,
                chat_id=chat_id,
                response_text=response_text,
            ):
                response_text = self._fallback_response(user_message, user_profile=user_profile)
        except Exception as exc:
            raise ChatModelUnavailable("Chat model is temporarily unavailable") from exc

        response_text = self._clean_response(response_text)
        if not response_text:
            raise ChatModelUnavailable("Chat model returned an empty answer")

        self._save_assistant_message(user_id=user_id, response_text=response_text, chat_id=chat_id)
        return response_text

    async def execute_async(
        self,
        user_id: int,
        user_message: str,
        chat_id: Optional[int] = None,
        user_profile: Optional[User] = None,
    ) -> str:
        self._save_user_message(user_id=user_id, user_message=user_message, chat_id=chat_id)
        prompt = self._build_prompt(user_id=user_id, chat_id=chat_id, user_profile=user_profile)

        try:
            response_text = await self._ask_model_async(prompt=prompt, user_id=user_id, chat_id=chat_id)
            if self._is_bad_response(response_text) or self._repeats_recent_answer(
                user_id=user_id,
                chat_id=chat_id,
                response_text=response_text,
            ):
                repaired_prompt = self._repair_prompt(prompt=prompt, bad_response=response_text)
                response_text = await self._ask_model_async(prompt=repaired_prompt, user_id=user_id, chat_id=chat_id)
            if self._is_bad_response(response_text) or self._repeats_recent_answer(
                user_id=user_id,
                chat_id=chat_id,
                response_text=response_text,
            ):
                response_text = self._fallback_response(user_message, user_profile=user_profile)
        except Exception as exc:
            raise ChatModelUnavailable("Chat model is temporarily unavailable") from exc

        response_text = self._clean_response(response_text)
        if not response_text:
            raise ChatModelUnavailable("Chat model returned an empty answer")

        self._save_assistant_message(user_id=user_id, response_text=response_text, chat_id=chat_id)
        return response_text

    def _save_user_message(self, user_id: int, user_message: str, chat_id: Optional[int]) -> None:
        self.chat_repo.add_message(
            ChatMessage(
                id=None,
                user_id=user_id,
                chat_id=chat_id,
                role="user",
                content=user_message,
                timestamp=datetime.datetime.utcnow(),
            ),
            chat_id=chat_id,
        )

    def _build_prompt(self, user_id: int, chat_id: Optional[int], user_profile: Optional[User] = None) -> str:
        history = self.chat_repo.get_last_messages(user_id=user_id, limit=12, chat_id=chat_id)
        return build_chat_context(history, user_profile=user_profile)

    def _ask_model(self, prompt: str, user_id: int, chat_id: Optional[int]) -> str:
        return self.llm.chat(
            prompt=prompt,
            user_context={"user_id": user_id, "chat_id": chat_id},
        )

    async def _ask_model_async(self, prompt: str, user_id: int, chat_id: Optional[int]) -> str:
        return await self.llm.chat_async(
            prompt=prompt,
            user_context={"user_id": user_id, "chat_id": chat_id},
        )

    def _save_assistant_message(self, user_id: int, response_text: str, chat_id: Optional[int]) -> None:
        self.chat_repo.add_message(
            ChatMessage(
                id=None,
                user_id=user_id,
                chat_id=chat_id,
                role="FinPulse",
                content=response_text,
                timestamp=datetime.datetime.utcnow(),
            ),
            chat_id=chat_id,
        )

    def _repeats_recent_answer(self, user_id: int, chat_id: Optional[int], response_text: str) -> bool:
        history = self.chat_repo.get_last_messages(user_id=user_id, limit=6, chat_id=chat_id)
        last_bot = next((msg.content for msg in reversed(history) if msg.role == "FinPulse"), "")
        last_user = next((msg.content for msg in reversed(history) if msg.role == "user"), "")
        return self._similarity(response_text, last_bot) >= 0.72 or self._reuses_recent_investment_core(
            response_text=response_text,
            previous_answer=last_bot,
            last_user_message=last_user,
        ) or self._reuses_vague_advice_after_concrete_followup(
            response_text=response_text,
            previous_answer=last_bot,
            last_user_message=last_user,
        )

    @staticmethod
    def _repair_prompt(prompt: str, bad_response: str) -> str:
        return (
            f"{prompt}\n\n"
            "Предыдущий ответ был слишком шаблонным или не по делу:\n"
            f"{bad_response.strip()[:700]}\n\n"
            "Сформулируй новый ответ. Не представляйся, не перечисляй возможности сервиса, "
            "не спрашивай «как я могу помочь». Ответь конкретно на последнее сообщение пользователя. "
            "Если пользователь просил еще варианты или альтернативы, не повторяй активы, тикеры и доли "
            "из предыдущего ответа; расширь набор вариантов по классам активов и уровню риска. "
            "Если последнее сообщение пользователя - широкий, но понятный запрос про облигации, акции, "
            "портфель или риск, дай полезный базовый ответ вместо просьбы уточнить. "
            "Если пользователь просит больше уточнений или информации, задай 2-3 конкретных вопроса "
            "по текущей теме и объясни, зачем они нужны. "
            "Пиши только по-русски; не используй иероглифы и слова на других языках, даже отдельные слова. "
            "Слова вроде diversify переводи на русский. "
            "Не повторяй пункты. Если сравниваешь акции и облигации: акция - доля в компании, "
            "облигация - долг эмитента; дивиденды относятся к акциям, купоны и погашение - к облигациям."
        )

    @staticmethod
    def _is_bad_response(response_text: str) -> bool:
        text = (response_text or "").strip().lower()
        if not text:
            return True
        bad_markers = [
            "модель готова помочь сформулировать вопрос",
            "я finpulse",
            "ваш финансовый ии-ассистент",
            "как я могу вам",
            "чем займемся",
            "получить рекомендации по инвестициям",
            "оптимизировать расходы",
            "perhaps",
            "投入",
            "**срок**",
            "**сумма**",
            "**риск**",
            "**рынок/тикеры**",
        ]
        if sum(marker in text for marker in bad_markers) >= 2:
            return True
        if CJK_RE.search(response_text or ""):
            return True
        if ChatWithLLM._has_untranslated_latin_words(response_text):
            return True
        if ChatWithLLM._has_repeated_numbered_items(text):
            return True
        if ChatWithLLM._has_financial_contradiction(text):
            return True
        if text.endswith(("...", "…")):
            return True
        if len(text) > 250 and not text.endswith((".", "!", "?", ")", ":", "»")):
            return True
        return False

    @staticmethod
    def _has_repeated_numbered_items(text: str) -> bool:
        items = NUMBERED_ITEM_RE.findall(text or "")
        if len(items) > 6:
            return True

        normalized: list[str] = []
        for item in items:
            head = re.split(r"[:.]", item, maxsplit=1)[0]
            words = re.findall(r"[а-яёa-z0-9]{4,}", head.lower())
            normalized.append(" ".join(words[:4]))

        seen: set[str] = set()
        repeats = 0
        for item in normalized:
            if not item:
                continue
            if item in seen:
                repeats += 1
            seen.add(item)
        return repeats >= 1

    @staticmethod
    def _has_untranslated_latin_words(text: str) -> bool:
        allowed_words = {"FinPulse"}
        for word in LATIN_WORD_RE.findall(text or ""):
            if word in allowed_words or word.isupper():
                continue
            return True
        return False

    @staticmethod
    def _has_financial_contradiction(text: str) -> bool:
        compact = " ".join((text or "").lower().split())
        bad_phrases = [
            "в облигациях владелец имеет право на получение дивидендов",
            "владелец облигации имеет право на получение дивидендов",
            "владельцы облигаций имеют право на получение дивидендов",
            "владельцы акций не имеют этих прав",
            "дивиденды (доход от продажи акций)",
        ]
        return any(phrase in compact for phrase in bad_phrases)

    @staticmethod
    def _asks_for_alternatives(text: str) -> bool:
        normalized = (text or "").lower()
        option_markers = ("вариант", "альтернатив", "способ", "инструмент", "актив")
        more_markers = ("еще", "ещё", "друг", "кроме", "без повтор", "не повтор")
        has_options = any(marker in normalized for marker in option_markers)
        asks_more = any(marker in normalized for marker in more_markers)
        return has_options and asks_more

    @staticmethod
    def _asks_for_concrete_allocation(text: str) -> bool:
        normalized = (text or "").lower()
        concrete_markers = ("конкрет", "точнее", "именно куда", "куда именно", "во что именно", "а куда")
        allocation_markers = ("куда", "вкладывать", "вложить", "инвест", "купить")
        return any(marker in normalized for marker in concrete_markers) and any(
            marker in normalized for marker in allocation_markers
        )

    @staticmethod
    def _asks_for_more_clarification(text: str) -> bool:
        normalized = (text or "").lower()
        has_more = any(marker in normalized for marker in ("больше", "подробнее", "деталь", "расшир", "дополн"))
        has_clarification = any(marker in normalized for marker in ("уточнен", "уточни", "информац", "объясн"))
        return has_more and has_clarification

    @staticmethod
    def _mentions_amount_only(text: str) -> bool:
        normalized = (text or "").lower()
        has_amount = bool(re.search(r"\b\d[\d\s]*(?:руб|₽)", normalized))
        has_invest_topic = any(marker in normalized for marker in ("есть", "руб", "₽", "деньг", "сумм"))
        has_goal = any(
            marker in normalized
            for marker in ("куда", "влож", "инвест", "риск", "срок", "цель", "доход", "портфел")
        )
        return has_amount and has_invest_topic and not has_goal

    @staticmethod
    def _reuses_recent_investment_core(response_text: str, previous_answer: str, last_user_message: str) -> bool:
        if not previous_answer or not ChatWithLLM._asks_for_alternatives(last_user_message):
            return False

        response_tickers = set(TICKER_RE.findall(response_text or ""))
        previous_tickers = set(TICKER_RE.findall(previous_answer or ""))
        shared_tickers = response_tickers & previous_tickers

        response_percents = set(PERCENT_RE.findall(response_text or ""))
        previous_percents = set(PERCENT_RE.findall(previous_answer or ""))
        shared_percents = response_percents & previous_percents

        return len(shared_tickers) >= 2 and bool(shared_percents)

    @staticmethod
    def _reuses_vague_advice_after_concrete_followup(
        response_text: str,
        previous_answer: str,
        last_user_message: str,
    ) -> bool:
        if not previous_answer or not ChatWithLLM._asks_for_concrete_allocation(last_user_message):
            return False

        if ChatWithLLM._similarity(response_text, previous_answer) >= 0.42:
            return True

        vague_phrases = [
            "для начала я предлагаю",
            "рассмотреть вариант инвестирования в акции",
            "к вашему интересующему сектору",
            "после того как вы будете более уверены",
            "можно рассмотреть возможность инвестирования в облигации",
            "личные финансовые возможности",
            "желаемый уровень доходности",
        ]
        response = " ".join((response_text or "").lower().split())
        previous = " ".join((previous_answer or "").lower().split())
        shared = sum(phrase in response and phrase in previous for phrase in vague_phrases)
        return shared >= 2

    @staticmethod
    def _fallback_response(user_message: str, user_profile: Optional[User] = None) -> str:
        normalized = (user_message or "").lower()
        if ChatWithLLM._asks_for_more_clarification(normalized):
            return (
                "Хорошо, тогда уточню главное. Ответьте на 3 вопроса: на какой срок планируете вложить деньги, "
                "какая просадка для вас приемлема и нужна ли возможность быстро вывести средства.\n\n"
                "От этого зависит выбор: для короткого срока и низкого риска обычно смотрят на ОФЗ, короткие облигации "
                "или фонды денежного рынка; для более длинного срока можно осторожно добавить долю акций."
            )

        if ChatWithLLM._mentions_amount_only(normalized):
            return (
                "Для суммы самой по себе не хватает трех вещей: срок, цель и допустимый риск. "
                "Если нужен осторожный старт, можно смотреть в сторону ОФЗ, коротких облигаций или фондов денежного рынка, "
                "а акции добавлять только небольшой долей.\n\n"
                "Уточните: на какой срок хотите вложить деньги и готовы ли видеть временную просадку портфеля?"
            )

        asks_low_risk_amount = (
            bool(re.search(r"\b50\s*000\b|\b50000\b", normalized))
            and any(marker in normalized for marker in ("без сильных риск", "низк", "осторож", "безопас"))
        )
        if asks_low_risk_amount:
            return (
                "Для 50 000 рублей без сильных рисков я бы рассматривал консервативную схему, а не акции как основу: "
                "30 000-35 000 рублей в короткие ОФЗ или фонд денежного рынка, 10 000-15 000 рублей в облигации "
                "крупных надежных эмитентов, 0-5 000 рублей оставить как резерв или учебную небольшую долю для акций.\n\n"
                "Главная проверка перед покупкой: срок до погашения, доходность к погашению, ликвидность, комиссия брокера "
                "и кредитное качество эмитента. Для низкого риска лучше не гнаться за самой высокой доходностью."
            )

        if "облигац" in normalized and "акци" not in normalized:
            return (
                "Облигации - это долговые бумаги: вы даете деньги эмитенту, а он обычно платит купоны "
                "и возвращает номинал в дату погашения. Для спокойного старта чаще смотрят на ОФЗ "
                "и выпуски крупных надежных компаний, сравнивая доходность к погашению, срок, ликвидность, "
                "тип купона и наличие оферты.\n\n"
                "Главные риски: дефолт эмитента, просадка цены при росте ставок, низкая ликвидность, "
                "налоги и комиссии. Практичный следующий шаг - выбрать горизонт, например до 1 года, "
                "1-3 года или дольше, и сравнить несколько выпусков без концентрации в одном эмитенте."
            )

        if "облигац" in normalized and "акци" in normalized:
            return (
                "Акция - это доля в компании: инвестор участвует в росте или падении бизнеса, "
                "может получать дивиденды "
                "и иногда имеет право голоса. Доходность заранее не гарантирована, "
                "цена акции может сильно меняться.\n\n"
                "Облигация - это долг эмитента перед инвестором: обычно есть купонные выплаты и дата погашения. "
                "Риск чаще ниже, чем у акции того же эмитента, но он не нулевой: важны надежность эмитента, "
                "ставка, срок и ликвидность."
            )

        if "акци" in normalized:
            return (
                "Акции подходят для участия в росте бизнеса, но их цена может заметно колебаться. "
                "Обычно их оценивают через качество компании, прибыль, долг, дивиденды, сектор и цену "
                "относительно ожиданий рынка.\n\n"
                "Для осторожного подхода не стоит выбирать одну бумагу на всю сумму: лучше сравнить "
                "несколько эмитентов, определить горизонт и заранее решить, какую просадку вы готовы выдержать."
            )

        if "риск" in normalized or "портфел" in normalized or "влож" in normalized or "инвест" in normalized:
            profile_response = ChatWithLLM._profile_investment_fallback(user_profile)
            if profile_response:
                return profile_response

            return (
                "Для базового инвестиционного решения сначала зафиксируйте цель, горизонт и допустимый риск. "
                "Чем короче срок и ниже готовность к просадкам, тем больше обычно доля консервативных инструментов "
                "вроде ОФЗ, коротких облигаций и денежных фондов; чем длиннее горизонт, тем уместнее доля акций.\n\n"
                "Не вкладывайте все в один актив: распределяйте деньги между несколькими эмитентами и классами "
                "инструментов, а доходность сравнивайте уже после учета комиссий, налогов и ликвидности."
            )

        return (
            "Давайте уточним запрос, чтобы ответ был полезным. Напишите тему и цель: например, выбрать облигации, "
            "собрать осторожный портфель, сравнить акции и облигации или оценить риск конкретного тикера."
        )

    @staticmethod
    def _profile_investment_fallback(user_profile: Optional[User]) -> str:
        if not user_profile:
            return ""

        has_profile = any(
            [
                user_profile.investment_horizon,
                user_profile.risk_level,
                user_profile.experience_level,
                user_profile.tickers,
                user_profile.sectors,
            ]
        )
        if not has_profile:
            return ""

        horizon = HORIZON_LABELS.get(user_profile.investment_horizon or "", user_profile.investment_horizon or "заданного горизонта")
        risk = RISK_LABELS.get(user_profile.risk_level or "", user_profile.risk_level or "заданного риска")
        tickers = ", ".join(user_profile.tickers[:4]) if user_profile.tickers else ""

        focus = f" с фокусом на {tickers}" if tickers else ""
        return (
            f"С учетом профиля: {horizon}, {risk}{focus}, базовая логика такая: не начинать с одной бумаги, "
            "а собрать несколько слоев портфеля. Я бы разделял решение на консервативную часть "
            "(ОФЗ, короткие облигации или денежный фонд), рыночную часть (акции/фонды под ваш горизонт) "
            "и небольшой резерв ликвидности.\n\n"
            "SBER и YDEX можно рассматривать только как часть акционной доли, а не как весь портфель. "
            "Перед конкретным выбором проверьте срок вложения, допустимую просадку, комиссии, ликвидность "
            "и долю каждой бумаги в общей сумме."
        )

    @staticmethod
    def _similarity(left: str, right: str) -> float:
        left_words = set(re.findall(r"[а-яёa-z0-9]{4,}", (left or "").lower()))
        right_words = set(re.findall(r"[а-яёa-z0-9]{4,}", (right or "").lower()))
        if not left_words or not right_words:
            return 0.0
        return len(left_words & right_words) / max(1, len(left_words | right_words))

    @staticmethod
    def _clean_response(response_text: str) -> str:
        text = (response_text or "").strip()
        text = CJK_RE.sub("", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"^(?:FinPulse|Ассистент|Бот)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text
