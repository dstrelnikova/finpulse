from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from datetime import date, datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

from app.application.interfaces.llm import ILLMService
from app.application.use_cases.news_analytics import build_fast_news_analysis, looks_russian
from app.core.settings import settings
from app.core.constants import (
    CATEGORY_MACRO,
    CATEGORY_STOCKS,
    MARKET_RU,
    NEWS_SOURCES,
)
from app.domain.entities.news_block import NewsBlock, NewsIndicator
from app.domain.entities.user import User
from app.infrastructure.database.news_cache_repo_impl import NewsCacheRepoSQL
from app.infrastructure.database.news_repo_impl import NewsRepositorySQL
from app.infrastructure.llm.scraper_service import ScraperService
from app.infrastructure.news.rss_service import RssNewsItem, RssNewsService, rss_item_asof
from app.infrastructure.utils import slugify

_WS_RE = re.compile(r"\s+")

_ALLOWED_IMPACT = {"positive", "neutral", "negative"}
_ALLOWED_CONFIDENCE = {"low", "medium", "high"}
logger = logging.getLogger(__name__)


def _clean_and_truncate(text: str, max_chars: int = 8000) -> str:
    if not text:
        return ""
    text = _WS_RE.sub(" ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + " …"


def _safe_json_loads(s: str) -> Optional[dict]:
    s = (s or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.I)
        s = re.sub(r"\s*```$", "", s)
    try:
        return json.loads(s)
    except Exception:
        return None


def _build_summary_text(bullets: List[str], conclusion: Optional[str], risks: List[str]) -> str:
    parts: List[str] = []
    if bullets:
        parts.append("• " + "\n• ".join(bullets))
    if conclusion:
        parts.append(f"\nВывод: {conclusion}")
    if risks:
        parts.append("\nРиски:\n• " + "\n• ".join(risks))
    return "\n".join(parts).strip()


def _norm_choice(x: Optional[str], allowed: set[str]) -> Optional[str]:
    if not x:
        return None
    x = str(x).strip().lower()
    if x in allowed:
        return x
    if "|" in x:
        return None
    return None


class GetNewsFeed:
    """
    Ежедневный обзор рынка РФ (MVP):
    - raw_text режем
    - base-summary кэшируем в Postgres на день (url+category+date)
    - индикатор impact/confidence (не “совет”)
    """

    def __init__(
        self,
        scraper: ScraperService,
        llm: ILLMService,
        cache_repo: NewsCacheRepoSQL,
        news_repo: NewsRepositorySQL,
        rss: RssNewsService | None = None,
    ):
        self.scraper = scraper
        self.llm = llm
        self.cache_repo = cache_repo
        self.news_repo = news_repo
        self.rss = rss

    def _pick_sources(
        self,
        user: Optional[User],
        *,
        audience: str,
        max_blocks: int = 2,
    ) -> list[tuple[str, str, str]]:
        picked: list[tuple[str, str, str]] = []
        market_sources = NEWS_SOURCES.get(MARKET_RU, {})

        def _prefer_scrape_friendly(urls: list[str]) -> list[str]:
            non_rbc = [u for u in urls if "rbc.ru" not in u]
            return non_rbc or urls

        macro_urls = _prefer_scrape_friendly(market_sources.get(CATEGORY_MACRO, []))
        if macro_urls:
            if audience == "public":
                picked.append((MARKET_RU, CATEGORY_MACRO, macro_urls[0]))
            else:
                key = self._user_persona_key(user)
                idx = self._stable_index(key + "|macro", len(macro_urls))
                picked.append((MARKET_RU, CATEGORY_MACRO, macro_urls[idx]))

        stocks_urls = _prefer_scrape_friendly(market_sources.get(CATEGORY_STOCKS, []))
        if audience == "public":
            for url in stocks_urls:
                if len(picked) >= max_blocks:
                    break
                picked.append((MARKET_RU, CATEGORY_STOCKS, url))
        else:
            if stocks_urls:
                key = self._user_persona_key(user)
                start = self._stable_index(key + "|stocks", len(stocks_urls))
                rotated = stocks_urls[start:] + stocks_urls[:start]
                for url in rotated:
                    if len(picked) >= max_blocks:
                        break
                    picked.append((MARKET_RU, CATEGORY_STOCKS, url))

        return picked[:max_blocks]

    def _make_base_prompt(self, category: str, raw_text: str, user: Optional[User], audience: str) -> str:
        focus = (
            "Фокус: макро РФ (ставки, инфляция, бюджет, санкции, нефть как фактор для РФ, влияние на рынок акций)."
            if category == CATEGORY_MACRO
            else (
                "Фокус: корпоративные новости РФ (отчетности, дивиденды, сделки, "
                "регулирование, сектора и крупные эмитенты)."
            )
        )
        persona_hint = ""
        if audience == "personal" and user is not None:
            persona_hint = (
                "\nПрофиль пользователя:\n"
                f"- горизонт: {user.investment_horizon or 'не указан'}\n"
                f"- риск: {user.risk_level or 'не указан'}\n"
                f"- тикеры: {', '.join(user.tickers) if user.tickers else 'не указаны'}\n"
                f"- секторы: {', '.join(user.sectors) if user.sectors else 'не указаны'}\n"
                "Сделай вывод чуть более прикладным к профилю пользователя.\n"
            )

        return (
            "Ты — аналитик российского фондового рынка.\n"
            f"{focus}\n\n"
            "Твоя задача: структурировать информацию по статье без повторов.\n\n"
            "Верни СТРОГО JSON (без markdown, без пояснений), формат:\n"
            "{\n"
            '  "summary": "2-3 предложения: о чем статья (без выводов и рисков)",\n'
            '  "facts": ["3-6 пунктов: только факты/цифры/события (без интерпретаций)"],\n'
            '  "conclusion": "1-2 предложения: что это значит для инвестора/рынка РФ (не совет)",\n'
            '  "explanation": ["2-4 пункта: почему так / какие механизмы влияния"],\n'
            '  "risks": ["2-4 пункта: риски и неопределенности (не повторять facts)"],\n'
            '  "indicator": {\n'
            '    "impact": "neutral",\n'
            '    "confidence": "medium",\n'
            '    "rationale": ["2-4 причины оценки impact"]\n'
            "  }\n"
            "}\n\n"
            "Правила:\n"
            "- summary не должен содержать conclusion/risks.\n"
            "- facts не должны повторять summary дословно.\n"
            "- risks не должны быть перефразированными facts.\n"
            '- indicator.impact: одно из ["positive","neutral","negative"].\n'
            '- indicator.confidence: одно из ["low","medium","high"].\n'
            "- Это НЕ инвестиционный совет.\n\n"
            f"{persona_hint}\n"
            f"Текст статьи:\n{raw_text}"
        )

    def _get_or_build_base(
        self,
        market: str,
        category: str,
        url: str,
        user: Optional[User],
        *,
        audience: str,
        force: bool = False,
    ) -> dict:
        now = datetime.now(timezone.utc)
        today = now.date()
        hour_slot = now.replace(minute=0, second=0, microsecond=0).strftime("%Y%m%d%H")
        cache_category = f"{category}::aud={audience}::v=2::slot={hour_slot}"

        if not force:
            cached = self.cache_repo.get(cache_date=today, category=cache_category, url=url)
            if cached:
                payload = _safe_json_loads(cached.payload_json)
                if not isinstance(payload, dict):
                    payload = {}
                payload["_meta"] = {
                    "asof": today.isoformat(),
                    "title": cached.title,
                    "source": cached.source,
                    "url": cached.url,
                    "hour_slot": hour_slot,
                }
                return payload

        parsed = urlparse(url)
        source_name = parsed.netloc or url
        title = "Рынок РФ — макрообзор" if category == CATEGORY_MACRO else "Рынок РФ — обзор акций"

        raw_text = self.scraper.fetch_article_text(url)
        raw_text = _clean_and_truncate(raw_text or "", max_chars=15000)

        if not raw_text:
            payload = self._build_fallback_payload(
                title=title,
                source=source_name,
                url=url,
                audience=audience,
                reason="Источник временно недоступен",
            )
        elif not settings.NEWS_USE_LLM:
            payload = self._build_rules_payload(
                title=title,
                source=source_name,
                category=category,
                raw_text=raw_text,
                user=user,
                audience=audience,
            )
        else:
            try:
                prompt = self._make_base_prompt(category=category, raw_text=raw_text, user=user, audience=audience)
                llm_out = self.llm.chat(prompt)
                payload = _safe_json_loads(llm_out)
                if not isinstance(payload, dict):
                    payload = self._build_rules_payload(
                        title=title,
                        source=source_name,
                        category=category,
                        raw_text=raw_text,
                        user=user,
                        audience=audience,
                    )
            except Exception as e:
                logger.warning("LLM недоступен для %s: %s", url, e)
                payload = self._build_rules_payload(
                    title=title,
                    source=source_name,
                    category=category,
                    raw_text=raw_text,
                    user=user,
                    audience=audience,
                )

        is_fallback = bool(payload.get("_fallback"))
        payload_json = json.dumps(payload, ensure_ascii=False)

        # Для personal сохраняем даже fallback, чтобы не дергать тяжёлую генерацию на каждый рефреш.
        # Для public fallback не кэшируем, чтобы витрина быстрее самовосстанавливалась.
        should_cache = (not is_fallback) or audience == "personal"
        if should_cache:
            self.cache_repo.upsert(
                cache_date=today,
                market=market,
                category=cache_category,
                url=url,
                source=source_name,
                title=title,
                payload_json=payload_json,
            )

        # Публичную витрину обновляем только валидным контентом, чтобы не затирать рабочие карточки fallback-ом.
        if audience == "public" and not is_fallback:
            self.news_repo.upsert_by_url(
                url=url,
                title=title,
                slug=self._news_slug(title, url),
                source=source_name,
                payload_json=payload_json,
                asof=today,
                market=market,
                category=category,
                is_public=True,
            )

        payload["_meta"] = {
            "asof": today.isoformat(),
            "title": title,
            "source": source_name,
            "url": url,
            "hour_slot": hour_slot,
        }

        return payload

    def _apply_user_overlay(self, user: User, payload: Optional[dict]) -> dict:
        if not isinstance(payload, dict):
            payload = {}

        bullets = payload.get("facts") or payload.get("bullets") or []
        conclusion = payload.get("conclusion") or ""
        summary = payload.get("summary") or ""
        text_blob = (" ".join(map(str, bullets)) + " " + str(summary) + " " + str(conclusion)).upper()

        if user.tickers:
            matched = [t for t in user.tickers if t and t.upper() in text_blob]
            if matched:
                bullets = list(map(str, bullets))
                bullets.insert(0, f"Упоминаются тикеры из ваших интересов: {', '.join(matched)}")
                payload["facts"] = bullets
        else:
            bullets = list(map(str, bullets))
            bullets.insert(0, "Лента персонализирована под ваш профиль риска и горизонт инвестирования.")
            payload["facts"] = bullets

        return payload

    def execute(self, user: User, force: bool = False, audience: str = "personal") -> List[NewsBlock]:
        if audience == "personal":
            rss_blocks = self._personal_blocks_from_rss(user=user)
            return rss_blocks

        sources = self._pick_sources(user=user, audience=audience, max_blocks=2)
        payloads = [
            self._get_or_build_base(
                market=market,
                category=category,
                url=url,
                user=user,
                audience=audience,
                force=force,
            )
            for market, category, url in sources
        ]
        return self._blocks_from_payloads(user=user, audience=audience, sources=sources, payloads=payloads)

    async def execute_async(self, user: User, force: bool = False, audience: str = "personal") -> List[NewsBlock]:
        if audience == "personal":
            rss_blocks = await asyncio.to_thread(self._personal_blocks_from_rss, user)
            return rss_blocks

        sources = self._pick_sources(user=user, audience=audience, max_blocks=2)
        payloads = await asyncio.gather(
            *(
                asyncio.to_thread(
                    self._get_or_build_base,
                    market,
                    category,
                    url,
                    user,
                    audience=audience,
                    force=force,
                )
                for market, category, url in sources
            )
        )
        return self._blocks_from_payloads(user=user, audience=audience, sources=sources, payloads=list(payloads))

    def _personal_blocks_from_rss(self, user: User, max_blocks: int = 4) -> List[NewsBlock]:
        if self.rss is None:
            return []

        items = self.rss.fetch_latest(limit=max_blocks * 4)
        if not items:
            return []

        selected = self._select_personal_rss_items(items=items, user=user, max_blocks=max_blocks)
        blocks: List[NewsBlock] = []

        for item in selected:
            personalized_hint = self._personalized_hint(user)
            item_text, _has_full_text = self._rss_item_text(item)
            payload = build_fast_news_analysis(
                title=item.title,
                text=item_text,
                source=item.source,
                category=item.category,
                personalized_hint=personalized_hint,
            ).to_payload()
            payload = self._apply_user_overlay(user=user, payload=payload)

            indicator_obj = payload.get("indicator") or {}
            indicator = NewsIndicator(
                impact=_norm_choice(indicator_obj.get("impact"), _ALLOWED_IMPACT) or "neutral",
                confidence=_norm_choice(indicator_obj.get("confidence"), _ALLOWED_CONFIDENCE) or "low",
                rationale=[str(x).strip() for x in indicator_obj.get("rationale") or [] if str(x).strip()],
            )
            asof = rss_item_asof(item)
            news_id = f"{asof.isoformat()}-personal-rss-{hashlib.sha1(item.url.encode('utf-8')).hexdigest()[:12]}"

            blocks.append(
                NewsBlock(
                    id=news_id,
                    slug=item.slug,
                    title=f"Персонально: {item.title}",
                    source=item.source,
                    url=item.url,
                    summary=str(payload.get("summary") or item.summary or item.title).strip(),
                    bullets=[str(x).strip() for x in payload.get("facts") or [] if str(x).strip()][:5],
                    conclusion=str(payload.get("conclusion") or "").strip() or None,
                    risks=[str(x).strip() for x in payload.get("risks") or [] if str(x).strip()][:4],
                    indicator=indicator,
                    asof=asof,
                )
            )

        return blocks

    def _rss_item_text(self, item: RssNewsItem) -> tuple[str, bool]:
        scraped = ""
        if self.scraper is not None:
            try:
                scraped = _clean_and_truncate(self.scraper.fetch_article_text(item.url) or "", max_chars=8000)
            except Exception as e:
                logger.warning("RSS article scrape failed %s: %s", item.url, e)

        if self._is_usable_article_text(scraped, item.summary):
            return scraped, True
        return item.summary or item.title, False

    def build_public_rss_payload(self, item: RssNewsItem, *, use_llm: bool = True) -> dict:
        item_text, has_full_text = self._rss_item_text(item)
        fallback_payload = build_fast_news_analysis(
            title=item.title,
            text=item_text,
            source=item.source,
            category=item.category,
        ).to_payload()
        fallback_payload["_source_type"] = "rss+rules"

        if not (use_llm and settings.NEWS_USE_LLM and settings.NEWS_LLM_FOR_PUBLIC_RSS):
            return fallback_payload

        try:
            prompt = self._make_public_rss_prompt(item=item, article_text=item_text, has_full_text=has_full_text)
            llm_out = self.llm.chat(prompt)
            payload = _safe_json_loads(llm_out)
            if not isinstance(payload, dict):
                return fallback_payload
            payload = self._normalize_public_payload(payload=payload, fallback=fallback_payload)
            payload["_source_type"] = "rss+gigachat"
            payload["_content_quality"] = "full_text" if has_full_text else "rss_only"
            return payload
        except Exception as e:
            logger.warning("GigaChat public RSS analysis failed %s: %s", item.url, e)
            return fallback_payload

    @staticmethod
    def _make_public_rss_prompt(item: RssNewsItem, article_text: str, has_full_text: bool) -> str:
        content_quality = (
            "Доступен полный/расширенный текст источника. Анализируй именно его, RSS используй только как контекст."
            if has_full_text
            else (
                "Полный текст источника недоступен; доступен только RSS-анонс/заголовок. "
                "Не делай полноценный вывод, ставь confidence=low и явно укажи ограничение данных."
            )
        )
        return (
            "Ты — финансовый редактор-аналитик FinPulse для публичной ленты новостей российского рынка.\n\n"
            "Твоя задача — превратить исходную новость в короткую, точную и полезную карточку для инвестора.\n"
            "Работай строго по предоставленному тексту источника. Не добавляй факты, цифры, компании, даты, "
            "прогнозы или выводы, которых нет в тексте.\n\n"
            f"Качество входных данных: {content_quality}\n\n"
            "Если данных мало, честно укажи это в risks и снизь confidence.\n\n"
            "Верни СТРОГО валидный JSON без markdown, без комментариев и без текста вне JSON.\n\n"
            "Формат ответа:\n"
            "{\n"
            '  "summary": "2-3 коротких предложения: суть новости простым деловым языком",\n'
            '  "facts": [\n'
            '    "3-5 содержательных пунктов: что произошло, участники, цифры/даты и важные детали"\n'
            "  ],\n"
            '  "market_meaning": "2-3 предложения: канал влияния на рынок РФ, сектор, ставки или эмитента",\n'
            '  "affected_segments": [\n'
            '    "сегменты/сектора/инструменты, которых новость может касаться"\n'
            "  ],\n"
            '  "risks": [\n'
            '    "2-4 конкретных риска или сценария: что может изменить оценку и что надо отслеживать"\n'
            "  ],\n"
            '  "indicator": {\n'
            '    "impact": "positive|neutral|negative",\n'
            '    "confidence": "low|medium|high",\n'
            '    "importance": "low|medium|high",\n'
            '    "rationale": [\n'
            '      "2-4 конкретные причины оценки impact/importance: факт из текста -> рыночный механизм"\n'
            "    ]\n"
            "  },\n"
            '  "quality": {\n'
            '    "is_public_feed_worthy": true,\n'
            '    "is_technical_noise": false,\n'
            '    "reason": "коротко объясни, почему новость стоит или не стоит показывать в публичной ленте"\n'
            "  }\n"
            "}\n\n"
            "Правила:\n"
            "- Пиши по-русски.\n"
            "- Не используй инвестиционные рекомендации: нельзя “купить”, “продать”, “держать”.\n"
            "- Не обещай будущую доходность или движение цены.\n"
            "- Не делай сильный вывод из слабого RSS-анонса.\n"
            "- Если доступен полный текст, summary, facts, market_meaning, risks и rationale должны опираться "
            "на полный текст, "
            "а не на один заголовок.\n"
            "- Если полного текста нет, не выдавай догадки за анализ: summary должен быть коротким, "
            "facts — только о том, что явно известно, "
            "market_meaning осторожный, confidence=low.\n"
            "- facts должны быть только фактами, без рыночной интерпретации.\n"
            "- Каждый пункт facts должен быть понятен без чтения заголовка.\n"
            "- Если конкретных цифр/дат/участников мало, не оставляй facts пустым: "
            "укажи, что именно известно из источника, "
            "и отдельным пунктом какие детали источник не раскрывает.\n"
            "- Не заполняй facts общими фразами вроде “сведения предоставлены источником”, "
            "если можно сказать конкретнее.\n"
            "- market_meaning — интерпретация, но осторожная.\n"
            "- market_meaning должен объяснять механизм: через ставку, инфляцию, дивиденды, ликвидность, "
            "валюту, индекс, сектор или отчетность.\n"
            "- Не пиши общие фразы вроде “может повлиять на рынок” без объяснения как именно.\n"
            "- risks не должны повторять facts.\n"
            "- risks должны быть сценарными: что может пойти иначе, какие условия способны изменить сигнал.\n"
            "- impact оценивает информационный сигнал, а не будущую цену.\n"
            "- importance оценивает полезность новости для публичной ленты.\n"
            "- confidence оценивает уверенность в выводе по полноте текста.\n"
            "- Если текст похож на техническое сообщение, расписание, тестовый контур, параметры торговой "
            "инфраструктуры, служебное уведомление или дублирующий анонс, поставь:\n"
            '  quality.is_public_feed_worthy=false\n'
            '  quality.is_technical_noise=true\n'
            '  indicator.importance="low"\n'
            '  indicator.confidence="low"\n\n'
            "Критерии importance:\n"
            "- high: новость влияет на ставки, инфляцию, бюджет, санкции, крупные компании, дивиденды, "
            "отчетность, IPO, регулирование рынка, ликвидность или широкий индекс.\n"
            "- medium: новость важна для отдельного сектора, группы компаний или инфраструктуры рынка.\n"
            "- low: новость справочная, техническая, календарная, имиджевая или без конкретных последствий.\n\n"
            "Критерии impact:\n"
            "- positive: текст содержит фактор, который может поддержать ожидания по рынку/сектору.\n"
            "- negative: текст содержит фактор, который может усилить риски, давление, неопределенность "
            "или стоимость капитала.\n"
            "- neutral: влияние неоднозначное, справочное или недостаточно данных.\n\n"
            "Входные данные:\n"
            f"Источник: {item.source}\n"
            f"Категория: {item.category}\n"
            f"Полный текст доступен: {'да' if has_full_text else 'нет'}\n"
            f"Заголовок: {item.title}\n"
            f"RSS-анонс: {item.summary}\n"
            f"Текст для анализа:\n{_clean_and_truncate(article_text, max_chars=8000)}"
        )

    @staticmethod
    def _normalize_public_payload(*, payload: dict, fallback: dict) -> dict:
        def _string(value: object, default: str = "") -> str:
            text = str(value or "").strip()
            return text or default

        def _list(value: object, fallback_value: object, limit: int) -> list[str]:
            raw = value if isinstance(value, list) else fallback_value
            if not isinstance(raw, list):
                return []
            return [str(x).strip() for x in raw if str(x).strip()][:limit]

        indicator = payload.get("indicator") if isinstance(payload.get("indicator"), dict) else {}
        fallback_indicator = fallback.get("indicator") if isinstance(fallback.get("indicator"), dict) else {}
        quality = payload.get("quality") if isinstance(payload.get("quality"), dict) else {}
        impact = _norm_choice(indicator.get("impact"), _ALLOWED_IMPACT) or fallback_indicator.get("impact") or "neutral"
        confidence = (
            _norm_choice(indicator.get("confidence"), _ALLOWED_CONFIDENCE)
            or fallback_indicator.get("confidence")
            or "low"
        )
        importance = _norm_choice(indicator.get("importance"), _ALLOWED_CONFIDENCE) or confidence
        market_meaning = _string(
            payload.get("market_meaning"),
            payload.get("conclusion") or fallback.get("conclusion") or "",
        )
        affected_segments = _list(payload.get("affected_segments"), [], 5)

        is_public_feed_worthy = quality.get("is_public_feed_worthy")
        if not isinstance(is_public_feed_worthy, bool):
            is_public_feed_worthy = True
        is_technical_noise = quality.get("is_technical_noise")
        if not isinstance(is_technical_noise, bool):
            is_technical_noise = False

        facts = _list(payload.get("facts"), fallback.get("facts"), 5)
        if not facts:
            facts = GetNewsFeed._fallback_public_facts(
                summary=_string(payload.get("summary"), fallback.get("summary") or ""),
                market_meaning=market_meaning,
                risks=_list(payload.get("risks"), fallback.get("risks"), 4),
            )

        return {
            "summary": _string(payload.get("summary"), fallback.get("summary") or ""),
            "facts": facts,
            "conclusion": market_meaning,
            "market_meaning": market_meaning,
            "affected_segments": affected_segments,
            "risks": _list(payload.get("risks"), fallback.get("risks"), 4),
            "indicator": {
                "impact": impact,
                "confidence": confidence,
                "importance": importance,
                "rationale": _list(indicator.get("rationale"), fallback_indicator.get("rationale"), 4),
            },
            "quality": {
                "is_public_feed_worthy": is_public_feed_worthy,
                "is_technical_noise": is_technical_noise,
                "reason": _string(quality.get("reason"), ""),
            },
        }

    @staticmethod
    def _fallback_public_facts(*, summary: str, market_meaning: str, risks: list[str]) -> list[str]:
        facts: list[str] = []
        if summary:
            facts.append(summary)
        if market_meaning:
            facts.append(f"Рыночный смысл новости: {market_meaning}")
        if risks:
            facts.append(f"Ключевое ограничение данных: {risks[0]}")
        if not facts:
            facts.append("Источник не содержит достаточно конкретных деталей для расширенного списка фактов.")
        return facts[:3]

    @staticmethod
    def _is_usable_article_text(text: str, rss_summary: str) -> bool:
        text = (text or "").strip()
        if not text or not looks_russian(text):
            return False
        if len(text) < 350:
            return False
        if len(text) <= len(rss_summary or "") + 120:
            return False

        head = text[:1200].lower()
        navigation_markers = (
            "деятельность финансовые рынки документы",
            "контактная информация интернет-приемная",
            "бесплатно для звонков с мобильных телефонов",
            "пресс-центр министерство деятельность документы",
            "курсы валют акции товарный рынок индексы",
        )
        return not any(marker in head for marker in navigation_markers)

    @staticmethod
    def _select_personal_rss_items(items: list[RssNewsItem], user: User, max_blocks: int) -> list[RssNewsItem]:
        tickers = {t.upper() for t in user.tickers or [] if t}

        def score(item: RssNewsItem) -> tuple[int, int]:
            blob = f"{item.title} {item.summary}".upper()
            ticker_score = 2 if tickers and any(t in blob for t in tickers) else 0
            category_score = 1 if item.category == CATEGORY_STOCKS else 0
            return ticker_score, category_score

        ranked = sorted(items, key=score, reverse=True)
        selected: list[RssNewsItem] = []
        categories: set[str] = set()

        for item in ranked:
            if item.category not in categories or len(selected) >= 2:
                selected.append(item)
                categories.add(item.category)
            if len(selected) >= max_blocks:
                return selected

        for item in ranked:
            if item not in selected:
                selected.append(item)
            if len(selected) >= max_blocks:
                break
        return selected

    @staticmethod
    def _personalized_hint(user: Optional[User]) -> str | None:
        if user is None:
            return None
        profile_bits = []
        if user.risk_level:
            profile_bits.append(f"профиль риска: {user.risk_level}")
        if user.investment_horizon:
            profile_bits.append(f"горизонт: {user.investment_horizon}")
        if user.tickers:
            profile_bits.append(f"интересующие тикеры: {', '.join(user.tickers[:5])}")
        if not profile_bits:
            return None
        return "Учтен профиль пользователя: " + "; ".join(profile_bits) + "."

    def _blocks_from_payloads(
        self,
        *,
        user: User,
        audience: str,
        sources: list[tuple[str, str, str]],
        payloads: list[dict],
    ) -> List[NewsBlock]:
        blocks: List[NewsBlock] = []
        if not sources:
            return []

        for (_, category, url), payload in zip(sources, payloads):
            if not isinstance(payload, dict):
                payload = {}
            if audience == "personal":
                payload = self._apply_user_overlay(user=user, payload=payload)

            meta = payload.get("_meta") or {}
            title = meta.get("title") or (
                "Рынок РФ — макрообзор" if category == CATEGORY_MACRO else "Рынок РФ — обзор акций"
            )
            if audience == "personal":
                title = f"Персонально: {title}"
            source = meta.get("source") or (urlparse(url).netloc or url)
            asof = date.fromisoformat(meta["asof"]) if meta.get("asof") else None

            summary: str = (payload.get("summary") or "").strip()

            facts: List[str] = payload.get("facts") or payload.get("bullets") or []
            facts = [str(x).strip() for x in facts if str(x).strip()]

            conclusion: Optional[str] = payload.get("conclusion")
            conclusion = conclusion.strip() if isinstance(conclusion, str) else conclusion

            risks: List[str] = payload.get("risks") or []
            risks = [str(x).strip() for x in risks if str(x).strip()]

            indicator_obj = payload.get("indicator") or {}
            indicator: Optional[NewsIndicator] = None

            if isinstance(indicator_obj, dict):
                impact = _norm_choice(indicator_obj.get("impact"), _ALLOWED_IMPACT)
                confidence = _norm_choice(indicator_obj.get("confidence"), _ALLOWED_CONFIDENCE)

                if impact and confidence:
                    indicator = NewsIndicator(
                        impact=impact,
                        confidence=confidence,
                        rationale=indicator_obj.get("rationale") or [],
                    )

            if not summary:
                fallback = _build_summary_text(bullets=facts, conclusion=conclusion, risks=risks)
                summary = fallback or "Нет данных для обзора."

            asof_key = asof.isoformat() if asof else date.today().isoformat()
            url_key = hashlib.sha1(f"{audience}|{category}|{url}".encode("utf-8")).hexdigest()[:12]
            news_id = f"{asof_key}-{audience}-{category}-{url_key}"
            news_slug = self._news_slug(title, url)

            blocks.append(
                NewsBlock(
                    id=news_id,
                    slug=news_slug,
                    title=title,
                    source=source,
                    url=url,
                    summary=summary,
                    bullets=facts,
                    conclusion=conclusion,
                    risks=risks,
                    indicator=indicator,
                    asof=asof,
                )
            )

        return blocks

    @staticmethod
    def _build_fallback_payload(
        *,
        title: str,
        source: str,
        url: str,
        audience: str,
        reason: str,
    ) -> dict:
        summary_prefix = "Персональный обзор" if audience == "personal" else "Публичный обзор"
        return {
            "summary": f"{summary_prefix}: {title}. {reason}.",
            "facts": [
                f"Источник: {source}",
                f"Ссылка: {url}",
            ],
            "conclusion": "Показываем базовую карточку без AI-аналитики.",
            "risks": [
                reason,
            ],
            "indicator": {
                "impact": "neutral",
                "confidence": "low",
                "rationale": ["Недостаточно данных для уверенной оценки."],
            },
            "_fallback": True,
        }

    @staticmethod
    def _build_rules_payload(
        *,
        title: str,
        source: str,
        category: str,
        raw_text: str,
        user: Optional[User],
        audience: str,
    ) -> dict:
        personalized_hint = None
        if audience == "personal" and user is not None:
            profile_bits = []
            if user.risk_level:
                profile_bits.append(f"профиль риска: {user.risk_level}")
            if user.investment_horizon:
                profile_bits.append(f"горизонт: {user.investment_horizon}")
            if user.tickers:
                profile_bits.append(f"интересующие тикеры: {', '.join(user.tickers[:5])}")
            if profile_bits:
                personalized_hint = "Учтен профиль пользователя: " + "; ".join(profile_bits) + "."

        payload = build_fast_news_analysis(
            title=title,
            text=raw_text,
            source=source,
            category=category,
            personalized_hint=personalized_hint,
        ).to_payload()
        payload["_source_type"] = "rules_fallback"
        return payload

    @staticmethod
    def _stable_index(seed: str, size: int) -> int:
        if size <= 0:
            return 0
        digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % size

    @staticmethod
    def _news_slug(title: str, url: str) -> str:
        suffix = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
        base = slugify(title) or "news"
        return f"{base}-{suffix}"

    @staticmethod
    def _user_persona_key(user: Optional[User]) -> str:
        if user is None:
            return "public"
        parts = [
            str(user.id or 0),
            user.investment_horizon or "",
            user.risk_level or "",
            ",".join(sorted(user.tickers or [])),
            ",".join(sorted(user.sectors or [])),
        ]
        return "|".join(parts)
