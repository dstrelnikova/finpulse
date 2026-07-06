from datetime import datetime, timezone

from app.application.use_cases.summarize_article import GetNewsFeed
from app.core.constants import CATEGORY_MACRO, MARKET_RU
from app.core.settings import settings
from app.infrastructure.news.rss_service import RssNewsItem


class _Scraper:
    def fetch_article_text(self, url: str) -> str:
        return (
            "Банк России сохранил ключевую ставку. Регулятор отметил устойчивое инфляционное давление "
            "и необходимость сохранять жесткие денежно-кредитные условия. В сообщении говорится, что "
            "текущая динамика цен остается важным фактором для денежно-кредитной политики. Банк России "
            "указывает, что дальнейшие решения будут приниматься с учетом устойчивости инфляции, ожиданий "
            "населения и кредитной активности. Для рынка это важно, потому что ставка влияет на стоимость "
            "заемного капитала, доходности облигаций и оценки акций."
        )


class _LLM:
    def chat(self, prompt: str, user_context=None) -> str:
        assert "Верни СТРОГО валидный JSON" in prompt
        assert "Полный текст доступен: да" in prompt
        assert "Анализируй именно его" in prompt
        return """
        {
          "summary": "Банк России сохранил ключевую ставку и указал на устойчивое инфляционное давление.",
          "facts": [
            "Банк России сохранил ключевую ставку; решение принято на фоне устойчивого инфляционного давления.",
            "Регулятор указал на необходимость сохранять жесткие денежно-кредитные условия."
          ],
          "market_meaning": "Для рынка РФ это поддерживает осторожный взгляд на стоимость капитала.",
          "affected_segments": ["широкий рынок акций", "облигации"],
          "risks": ["В тексте нет деталей по будущей траектории ставки."],
          "indicator": {
            "impact": "negative",
            "confidence": "medium",
            "importance": "high",
            "rationale": ["Жесткие денежно-кредитные условия давят на оценки активов."]
          },
          "quality": {
            "is_public_feed_worthy": true,
            "is_technical_noise": false,
            "reason": "Новость касается ключевой ставки."
          }
        }
        """


def test_public_rss_payload_uses_llm_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "NEWS_USE_LLM", True)
    monkeypatch.setattr(settings, "NEWS_LLM_FOR_PUBLIC_RSS", True)

    use_case = GetNewsFeed(
        scraper=_Scraper(),
        llm=_LLM(),
        cache_repo=None,
        news_repo=None,
        rss=None,
    )
    item = RssNewsItem(
        title="Банк России сохранил ставку",
        url="https://example.test/news",
        source="Test",
        category=CATEGORY_MACRO,
        market=MARKET_RU,
        summary="Короткий RSS-анонс.",
        published_at=datetime(2026, 4, 27, tzinfo=timezone.utc),
        slug="bank-rossii-sohranil-stavku",
    )

    payload = use_case.build_public_rss_payload(item)

    assert payload["_source_type"] == "rss+gigachat"
    assert payload["indicator"]["impact"] == "negative"
    assert payload["indicator"]["confidence"] == "medium"
    assert payload["indicator"]["importance"] == "high"
    assert payload["quality"]["is_public_feed_worthy"] is True
    assert payload["_content_quality"] == "full_text"
    assert payload["affected_segments"] == ["широкий рынок акций", "облигации"]
    assert len(payload["facts"]) == 2
    assert "ключевую ставку" in payload["facts"][0]
    assert payload["summary"].startswith("Банк России")


def test_public_rss_payload_falls_back_to_rules_on_bad_llm(monkeypatch):
    monkeypatch.setattr(settings, "NEWS_USE_LLM", True)
    monkeypatch.setattr(settings, "NEWS_LLM_FOR_PUBLIC_RSS", True)

    class BadLLM:
        def chat(self, prompt: str, user_context=None) -> str:
            return "not json"

    use_case = GetNewsFeed(
        scraper=_Scraper(),
        llm=BadLLM(),
        cache_repo=None,
        news_repo=None,
        rss=None,
    )
    item = RssNewsItem(
        title="Банк России сохранил ставку",
        url="https://example.test/news",
        source="Test",
        category=CATEGORY_MACRO,
        market=MARKET_RU,
        summary="Короткий RSS-анонс.",
        published_at=None,
        slug="bank-rossii-sohranil-stavku",
    )

    payload = use_case.build_public_rss_payload(item)

    assert payload["_source_type"] == "rss+rules"
    assert payload["summary"]


def test_public_rss_prompt_marks_rss_only_when_full_text_unavailable():
    item = RssNewsItem(
        title="Короткая новость",
        url="https://example.test/news",
        source="Test",
        category=CATEGORY_MACRO,
        market=MARKET_RU,
        summary="Короткий RSS-анонс.",
        published_at=None,
        slug="short-news",
    )

    prompt = GetNewsFeed._make_public_rss_prompt(
        item=item,
        article_text=item.summary,
        has_full_text=False,
    )

    assert "Полный текст доступен: нет" in prompt
    assert "confidence=low" in prompt
    assert "не выдавай догадки за анализ" in prompt
