import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Сервис для получения и очистки текста статьи по URL.
    """

    def fetch_article_text(self, url: str) -> str | None:
        """
        Загружает страницу по URL и возвращает очищенный текст статьи.
        При ошибке возвращает None (НЕ выбрасывает исключение).
        """
        try:
            response = requests.get(
                url,
                timeout=12,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; FinPulseBot/1.0; +https://finpulse.local)",
                    "Accept-Language": "ru,en;q=0.8",
                },
            )
            response.raise_for_status()

        except Exception as e:
            logger.warning(f"[Scraper] Не удалось загрузить статью {url}: {e}")
            return None  # <-- ключевое изменение

        soup = BeautifulSoup(response.text, "html.parser")

        # Удаляем мусорные теги
        for tag in soup(["script", "style", "noscript", "header", "footer", "form", "nav", "aside", "svg"]):
            tag.extract()

        candidates = []
        selectors = [
            "article",
            "main",
            "[itemprop='articleBody']",
            ".article__text",
            ".article__body",
            ".article-content",
            ".article__content",
            ".news-detail",
            ".material",
            ".b-article__text",
            ".doc__text",
            ".js-mediator-article",
        ]
        for selector in selectors:
            for node in soup.select(selector):
                text = node.get_text(separator=" ", strip=True)
                if text:
                    candidates.append(text)

        for meta_name in ("description", "og:description"):
            meta = soup.find("meta", attrs={"name": meta_name}) or soup.find("meta", attrs={"property": meta_name})
            content = meta.get("content") if meta else None
            if content:
                candidates.append(content)

        if not candidates:
            candidates.append(soup.get_text(separator=" ", strip=True))

        text = max(candidates, key=len)

        cleaned = " ".join(text.split())
        cleaned = self._drop_repeated_boilerplate(cleaned)

        return cleaned or None

    @staticmethod
    def _drop_repeated_boilerplate(text: str) -> str:
        text = re.sub(r"\b(Поделиться|Реклама|Новости|Читайте также|Все новости)\b", " ", text, flags=re.I)
        text = re.sub(r"\s+", " ", text).strip()
        return text
