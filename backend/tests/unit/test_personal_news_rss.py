from datetime import datetime, timezone

from app.application.use_cases.summarize_article import GetNewsFeed
from app.core.constants import CATEGORY_STOCKS, MARKET_RU
from app.domain.entities.user import User
from app.infrastructure.news.rss_service import RssNewsItem


class _FakeRss:
    def fetch_latest(self, limit: int = 30):
        return [
            RssNewsItem(
                title="Московская биржа сообщила о новых режимах торгов",
                url="https://example.test/news/real-item",
                source="Московская биржа",
                category=CATEGORY_STOCKS,
                market=MARKET_RU,
                summary="Биржа раскрыла детали изменения режимов торгов для российского рынка.",
                published_at=datetime(2026, 4, 27, tzinfo=timezone.utc),
                slug="real-item",
            )
        ]


class _EmptyRss:
    def fetch_latest(self, limit: int = 30):
        return []


class _ExplodingScraper:
    def fetch_article_text(self, url: str):
        raise AssertionError("personal feed must not scrape category pages when RSS is empty")


def test_personal_feed_uses_real_rss_news_titles():
    use_case = GetNewsFeed(
        scraper=None,
        llm=None,
        cache_repo=None,
        news_repo=None,
        rss=_FakeRss(),
    )
    user = User(
        id=1,
        name="Darya",
        email="darya@example.com",
        password_hash="",
        risk_level="medium",
        investment_horizon="short",
        tickers=["SBER"],
    )

    blocks = use_case.execute(user=user, audience="personal")

    assert len(blocks) == 1
    assert blocks[0].title == "Персонально: Московская биржа сообщила о новых режимах торгов"
    assert "Рынок РФ — обзор акций" not in blocks[0].title
    assert "Биржа раскрыла детали" in blocks[0].summary


def test_personal_feed_does_not_fallback_to_category_pages_when_rss_empty():
    use_case = GetNewsFeed(
        scraper=_ExplodingScraper(),
        llm=None,
        cache_repo=None,
        news_repo=None,
        rss=_EmptyRss(),
    )
    user = User(id=1, name="Darya", email="darya@example.com", password_hash="")

    assert use_case.execute(user=user, audience="personal") == []
