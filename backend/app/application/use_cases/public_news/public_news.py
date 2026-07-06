import json
import logging
import threading
import time
from datetime import date, timedelta
from typing import List, Optional

from app.application.use_cases.news_analytics import looks_like_technical_news, looks_russian
from app.application.use_cases.summarize_article import GetNewsFeed
from app.core.settings import settings
from app.domain.entities.user import User
from app.infrastructure.database.news_repo_impl import NewsRepositorySQL
from app.infrastructure.news.rss_service import RssNewsService, rss_item_asof
from app.presentation.schemas.summary import NewsBlockOut

logger = logging.getLogger(__name__)
_PUBLIC_REFRESH_LOCK = threading.Lock()
_PUBLIC_REFRESH_COOLDOWN_SEC = 5 * 60
_LAST_PUBLIC_REFRESH_TS = 0.0

_LOW_INFO_MARKERS = (
    "мало проверяемых фактов",
    "недостаточно конкретных",
    "не содержит достаточно конкретных",
    "детали не раскры",
    "нет конкретной информации",
    "точное содержание",
    "подробности лучше сверить",
    "подробности доступны в источнике",
    "источник не раскрывает",
    "в анонсе мало",
    "rss-анонс",
    "короткий анонс",
)

_GENERIC_FACT_PREFIXES = (
    "сведения предоставлены",
    "источник:",
    "тема:",
    "материал:",
    "текст анонса содержит",
    "конкретная величина",
    "нет конкретной",
)

_LOW_VALUE_TITLE_MARKERS = (
    "информация о работе платежной системы",
    "график работы платежной системы",
    "режим работы платежной системы",
)

_CONFIDENCE_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


class GetPublicNewsFeed:
    def __init__(self, repo: NewsRepositorySQL, rss: RssNewsService, generator: GetNewsFeed):
        self.repo = repo
        self.rss = rss
        self.generator = generator

    def execute(self, limit: int = 50, force: bool = False) -> List[NewsBlockOut]:
        items = self._russian_items(limit=limit)

        if force:
            self._refresh_public(force=True)
            return self._russian_items(limit=limit)

        # Cold start: если данных нет, делаем синхронное наполнение один раз.
        if not items:
            self._refresh_public(force=False)
            return self._russian_items(limit=limit)

        # Stale-while-revalidate: отдаём витрину мгновенно, обновляем в фоне.
        self._refresh_public_in_background()
        return items

    def refresh(self, *, force: bool = False) -> None:
        self._refresh_public(force=force)

    def _russian_items(self, limit: int) -> List[NewsBlockOut]:
        rows = self.repo.list_public(limit=limit * 10)
        out: list[NewsBlockOut] = []
        for row in rows:
            item = self.repo.to_news_block_out(row)
            if self._is_public_item_eligible(item):
                out.append(item)
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def _is_public_item_eligible(item: NewsBlockOut) -> bool:
        blob = f"{item.title} {item.summary}"
        if not looks_russian(blob):
            return False

        if item.asof and item.asof < date.today() - timedelta(days=settings.NEWS_PUBLIC_MAX_AGE_DAYS):
            return False

        url = (item.url or "").lower().rstrip("/")
        source = (item.source or "").lower()
        title = (item.title or "").lower()

        if any(marker in title for marker in _LOW_VALUE_TITLE_MARKERS):
            return False

        # Старый fallback по общей странице МосБиржи дает техническую витрину,
        # а не конкретную публичную новость.
        if url == "https://www.moex.com/ru/news" or (
            "moex.com" in source and title.startswith("рынок рф")
        ):
            return False

        if looks_like_technical_news(item.title, item.summary, item.source):
            return False

        if not GetPublicNewsFeed._passes_min_confidence(item):
            return False

        if GetPublicNewsFeed._is_low_information_item(item):
            return False

        return True

    @staticmethod
    def _passes_min_confidence(item: NewsBlockOut) -> bool:
        confidence = item.indicator.confidence if item.indicator else "low"
        impact = item.indicator.impact if item.indicator else "neutral"
        min_confidence = settings.NEWS_PUBLIC_MIN_CONFIDENCE.lower().strip()
        if impact == "negative" and confidence == "low":
            return len(GetPublicNewsFeed._meaningful_facts(item.bullets)) >= settings.NEWS_PUBLIC_MIN_FACTS
        return _CONFIDENCE_RANK.get(confidence, 0) >= _CONFIDENCE_RANK.get(min_confidence, 2)

    @staticmethod
    def _confidence_passes_threshold(confidence: str) -> bool:
        min_confidence = settings.NEWS_PUBLIC_MIN_CONFIDENCE.lower().strip()
        return _CONFIDENCE_RANK.get(confidence, 0) >= _CONFIDENCE_RANK.get(min_confidence, 2)

    @staticmethod
    def _is_low_information_item(item: NewsBlockOut) -> bool:
        text = " ".join(
            [
                item.title or "",
                item.summary or "",
                item.conclusion or "",
                " ".join(item.bullets or []),
                " ".join(item.risks or []),
                " ".join(item.indicator.rationale if item.indicator else []),
            ]
        ).lower()

        if any(marker in text for marker in _LOW_INFO_MARKERS):
            return True

        meaningful_facts = GetPublicNewsFeed._meaningful_facts(item.bullets)
        if len(meaningful_facts) < settings.NEWS_PUBLIC_MIN_FACTS:
            confidence = item.indicator.confidence if item.indicator else "low"
            if confidence == "low":
                return True

        return False

    @staticmethod
    def _meaningful_facts(facts: list[str] | None) -> list[str]:
        out: list[str] = []
        for fact in facts or []:
            normalized = str(fact or "").strip().lower()
            if not normalized:
                continue
            if len(normalized) < 35:
                continue
            if normalized.startswith(_GENERIC_FACT_PREFIXES):
                continue
            if any(marker in normalized for marker in _LOW_INFO_MARKERS):
                continue
            out.append(fact)
        return out

    def _refresh_public(self, *, force: bool) -> None:
        rss_count = self._refresh_from_rss(limit=40)
        if rss_count:
            return

        public_user = User(
            id=0,
            name="Public",
            email="public@finpulse.local",
            password_hash="",
        )
        self.generator.execute(public_user, force=force, audience="public")

    def _refresh_from_rss(self, limit: int) -> int:
        count = 0
        for item in self.rss.fetch_latest(limit=limit):
            if looks_like_technical_news(item.title, item.summary, item.source):
                continue
            payload = self.generator.build_public_rss_payload(
                item,
                use_llm=count < settings.NEWS_PUBLIC_RSS_LLM_LIMIT,
            )
            if not self._is_payload_public_worthy(payload):
                continue
            self.repo.upsert_by_url(
                url=item.url,
                title=item.title,
                slug=item.slug,
                source=item.source,
                payload_json=json.dumps(payload, ensure_ascii=False),
                asof=rss_item_asof(item),
                market=item.market,
                category=item.category,
                is_public=True,
            )
            count += 1
        return count

    @staticmethod
    def _is_payload_public_worthy(payload: dict) -> bool:
        quality = payload.get("quality") if isinstance(payload, dict) else {}
        if not isinstance(quality, dict):
            return True
        if quality.get("is_public_feed_worthy") is False:
            return False
        if quality.get("is_technical_noise") is True:
            return False

        text = " ".join(
            [
                str(payload.get("summary") or ""),
                str(payload.get("conclusion") or ""),
                str(payload.get("market_meaning") or ""),
                " ".join(map(str, payload.get("facts") or [])),
                " ".join(map(str, payload.get("risks") or [])),
                str(quality.get("reason") or ""),
            ]
        ).lower()
        if any(marker in text for marker in _LOW_INFO_MARKERS):
            return False

        indicator = payload.get("indicator") if isinstance(payload.get("indicator"), dict) else {}
        confidence = str(indicator.get("confidence") or "low").lower()
        importance = str(indicator.get("importance") or confidence).lower()
        facts = GetPublicNewsFeed._meaningful_facts([str(x) for x in payload.get("facts") or []])

        if not GetPublicNewsFeed._confidence_passes_threshold(confidence):
            return False

        if settings.NEWS_PUBLIC_HIDE_RSS_ONLY_LOW_INFO and payload.get("_content_quality") == "rss_only":
            if confidence == "low" or importance == "low" or len(facts) < settings.NEWS_PUBLIC_MIN_FACTS:
                return False

        if len(facts) < settings.NEWS_PUBLIC_MIN_FACTS and confidence == "low":
            return False
        return True

    def _refresh_public_in_background(self) -> None:
        global _LAST_PUBLIC_REFRESH_TS

        now = time.monotonic()
        if now - _LAST_PUBLIC_REFRESH_TS < _PUBLIC_REFRESH_COOLDOWN_SEC:
            return

        if not _PUBLIC_REFRESH_LOCK.acquire(blocking=False):
            return
        _LAST_PUBLIC_REFRESH_TS = now

        def _runner() -> None:
            try:
                self._refresh_public(force=False)
            except Exception as e:
                logger.warning("Background public news refresh failed: %s", e)
            finally:
                _PUBLIC_REFRESH_LOCK.release()

        thread = threading.Thread(target=_runner, name="public-news-refresh", daemon=True)
        thread.start()


class GetPublicNewsItem:
    def __init__(self, repo: NewsRepositorySQL):
        self.repo = repo

    def execute(self, news_id: int) -> Optional[NewsBlockOut]:
        i = self.repo.get_public_by_id(news_id)
        if not i:
            return None
        item = self.repo.to_news_block_out(i)
        return item if looks_russian(f"{item.title} {item.summary}") else None


class GetPublicNewsItemBySlug:
    def __init__(self, repo: NewsRepositorySQL):
        self.repo = repo

    def execute(self, slug: str) -> Optional[NewsBlockOut]:
        i = self.repo.get_public_by_slug(slug=slug)
        if not i:
            return None
        item = self.repo.to_news_block_out(i)
        return item if looks_russian(f"{item.title} {item.summary}") else None
