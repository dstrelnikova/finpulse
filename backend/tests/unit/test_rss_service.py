from app.core.constants import CATEGORY_MACRO, MARKET_RU, RssNewsSource
from app.infrastructure.news.rss_service import RssNewsService


class _Response:
    def __init__(self, text: str):
        self.text = text
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        return None


def test_rss_service_parses_and_cleans_rss(monkeypatch):
    xml = """
    <rss version="2.0">
      <channel>
        <item>
          <title>Ключевая ставка сохранена</title>
          <link>https://example.test/news/1</link>
          <description><![CDATA[<p>Совет директоров сохранил ставку.</p>]]></description>
          <pubDate>Mon, 27 Apr 2026 10:00:00 +0300</pubDate>
        </item>
      </channel>
    </rss>
    """

    monkeypatch.setattr("app.infrastructure.news.rss_service.requests.get", lambda *args, **kwargs: _Response(xml))

    service = RssNewsService(
        sources=[RssNewsSource(name="Test", url="https://example.test/rss", category=CATEGORY_MACRO)],
        per_source_limit=5,
    )

    items = service.fetch_latest()

    assert len(items) == 1
    assert items[0].title == "Ключевая ставка сохранена"
    assert items[0].summary == "Совет директоров сохранил ставку."
    assert items[0].url == "https://example.test/news/1"
    assert items[0].market == MARKET_RU
    assert items[0].slug.startswith("ключевая-ставка-сохранена-")


def test_rss_service_deduplicates_by_url(monkeypatch):
    xml = """
    <rss version="2.0">
      <channel>
        <item><title>Ставка сохранена</title><link>https://example.test/a</link></item>
        <item><title>Ставка сохранена копия</title><link>https://example.test/a</link></item>
      </channel>
    </rss>
    """

    monkeypatch.setattr("app.infrastructure.news.rss_service.requests.get", lambda *args, **kwargs: _Response(xml))

    service = RssNewsService(
        sources=[RssNewsSource(name="Test", url="https://example.test/rss", category=CATEGORY_MACRO)],
        per_source_limit=5,
    )

    assert len(service.fetch_latest()) == 1


def test_rss_service_skips_english_items(monkeypatch):
    xml = """
    <rss version="2.0">
      <channel>
        <item>
          <title>Risk parameters change for the security SU26231RMFS9</title>
          <link>https://example.test/en</link>
          <description>As per the Securities market risk parameters methodology...</description>
        </item>
      </channel>
    </rss>
    """

    monkeypatch.setattr("app.infrastructure.news.rss_service.requests.get", lambda *args, **kwargs: _Response(xml))

    service = RssNewsService(
        sources=[RssNewsSource(name="Test", url="https://example.test/rss", category=CATEGORY_MACRO)],
        per_source_limit=5,
    )

    assert service.fetch_latest() == []


def test_rss_service_discovers_news_from_html_index(monkeypatch):
    html = """
    <html>
      <body>
        <a href="/economics/28/04/2026/test-news">Инфляционные ожидания населения снизились в апреле</a>
        <a href="/contacts">Контакты редакции</a>
      </body>
    </html>
    """

    monkeypatch.setattr("app.infrastructure.news.rss_service.requests.get", lambda *args, **kwargs: _Response(html))

    service = RssNewsService(
        sources=[RssNewsSource(name="РБК Экономика", url="https://www.rbc.ru/economics/", category=CATEGORY_MACRO)],
        per_source_limit=5,
    )

    items = service.fetch_latest()

    assert len(items) == 1
    assert items[0].title == "Инфляционные ожидания населения снизились в апреле"
    assert items[0].url == "https://www.rbc.ru/economics/28/04/2026/test-news"
