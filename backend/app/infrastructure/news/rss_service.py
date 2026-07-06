from __future__ import annotations

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable
from urllib.parse import urljoin
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.core.constants import PUBLIC_RSS_NEWS_SOURCES, RssNewsSource
from app.application.use_cases.news_analytics import looks_russian
from app.infrastructure.utils import slugify

logger = logging.getLogger(__name__)

_WS_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class RssNewsItem:
    title: str
    url: str
    source: str
    category: str
    market: str
    summary: str
    published_at: datetime | None
    slug: str


class RssNewsService:
    def __init__(
        self,
        sources: Iterable[RssNewsSource] = PUBLIC_RSS_NEWS_SOURCES,
        timeout_sec: int = 8,
        per_source_limit: int = 8,
    ):
        self.sources = list(sources)
        self.timeout_sec = timeout_sec
        self.per_source_limit = per_source_limit

    def fetch_latest(self, limit: int = 30) -> list[RssNewsItem]:
        items: list[RssNewsItem] = []
        seen_urls: set[str] = set()

        with ThreadPoolExecutor(max_workers=max(1, min(len(self.sources), 4))) as executor:
            futures = [executor.submit(self._fetch_source, source) for source in self.sources]
            for future in as_completed(futures):
                try:
                    source_items = future.result()
                except Exception as e:
                    logger.warning("RSS worker failed: %s", e)
                    continue

                for item in source_items:
                    if item.url in seen_urls:
                        continue
                    seen_urls.add(item.url)
                    items.append(item)

        items.sort(key=lambda i: i.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return items[: max(1, limit)]

    def _fetch_source(self, source: RssNewsSource) -> list[RssNewsItem]:
        try:
            response = requests.get(
                source.url,
                timeout=self.timeout_sec,
                headers={"User-Agent": "FinPulse/1.0 RSS reader"},
            )
            response.raise_for_status()
        except Exception as e:
            logger.warning("RSS source unavailable %s: %s", source.url, e)
            return []

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            logger.warning("RSS source returned invalid XML %s: %s", source.url, e)
            return self._parse_html_index(response.text, source)

        parsed_items = self._parse_rss(root, source)
        if not parsed_items:
            parsed_items = self._parse_atom(root, source)
        if not parsed_items:
            parsed_items = self._parse_html_index(response.text, source)

        return parsed_items[: self.per_source_limit]

    def _parse_html_index(self, html: str, source: RssNewsSource) -> list[RssNewsItem]:
        soup = BeautifulSoup(html or "", "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "form", "nav", "footer", "header"]):
            tag.extract()

        out: list[RssNewsItem] = []
        seen_urls: set[str] = set()
        for link_node in soup.find_all("a", href=True):
            title = self._clean_text(link_node.get_text(" ", strip=True), max_chars=220)
            href = urljoin(source.url, link_node.get("href") or "")
            if not self._is_probable_news_link(title=title, url=href, source_url=source.url):
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)
            out.append(
                RssNewsItem(
                    title=title,
                    url=href,
                    source=source.name,
                    category=source.category,
                    market=source.market,
                    summary=title,
                    published_at=None,
                    slug=self._slug(title=title, url=href),
                )
            )
            if len(out) >= self.per_source_limit:
                break
        return out

    @staticmethod
    def _is_probable_news_link(*, title: str, url: str, source_url: str) -> bool:
        if not title or len(title) < 28 or len(title) > 180:
            return False
        if not looks_russian(title):
            return False

        parsed = urlparse(url)
        source_host = urlparse(source_url).netloc.replace("www.", "")
        if source_host and source_host not in parsed.netloc.replace("www.", ""):
            return False

        lower = title.lower()
        bad_words = (
            "подписка",
            "реклама",
            "архив",
            "фото",
            "видео",
            "спецпроект",
            "rss",
            "контакты",
            "показать еще",
            "все новости",
        )
        if any(word in lower for word in bad_words):
            return False

        path = parsed.path.lower()
        return any(
            marker in path
            for marker in (
                "/economics/",
                "/finances/",
                "/business/",
                "/ekonomika",
                "/finance",
                "/doc/",
                "/news/",
            )
        )

    def _parse_rss(self, root: ET.Element, source: RssNewsSource) -> list[RssNewsItem]:
        out: list[RssNewsItem] = []
        for item in root.findall(".//item"):
            parsed = self._item_from_values(
                source=source,
                title=self._child_text(item, "title"),
                link=self._child_text(item, "link") or self._child_text(item, "guid"),
                summary=self._child_text(item, "description"),
                published=self._child_text(item, "pubDate") or self._child_text(item, "date"),
            )
            if parsed:
                out.append(parsed)
        return out

    def _parse_atom(self, root: ET.Element, source: RssNewsSource) -> list[RssNewsItem]:
        out: list[RssNewsItem] = []
        for entry in root.findall(".//{*}entry"):
            link = ""
            for link_node in entry.findall("{*}link"):
                href = link_node.attrib.get("href")
                if href:
                    link = href
                    break

            parsed = self._item_from_values(
                source=source,
                title=self._child_text(entry, "title"),
                link=link,
                summary=self._child_text(entry, "summary") or self._child_text(entry, "content"),
                published=self._child_text(entry, "published") or self._child_text(entry, "updated"),
            )
            if parsed:
                out.append(parsed)
        return out

    def _item_from_values(
        self,
        *,
        source: RssNewsSource,
        title: str,
        link: str,
        summary: str,
        published: str,
    ) -> RssNewsItem | None:
        title = self._clean_text(title, max_chars=300)
        link = urljoin(source.url, unescape(link or "").strip())
        summary = self._clean_text(summary, max_chars=700)

        if not title or not link:
            return None
        if not looks_russian(f"{title} {summary}"):
            return None

        return RssNewsItem(
            title=title,
            url=link,
            source=source.name,
            category=source.category,
            market=source.market,
            summary=summary or title,
            published_at=self._parse_datetime(published),
            slug=self._slug(title=title, url=link),
        )

    @staticmethod
    def _child_text(node: ET.Element, tag: str) -> str:
        found = node.find(tag)
        if found is None:
            found = node.find(f"{{*}}{tag}")
        return "".join(found.itertext()).strip() if found is not None else ""

    @staticmethod
    def _clean_text(value: str, max_chars: int) -> str:
        text = BeautifulSoup(unescape(value or ""), "html.parser").get_text(" ", strip=True)
        text = _WS_RE.sub(" ", text).strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 1].rstrip() + "…"

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        value = (value or "").strip()
        if not value:
            return None

        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _slug(title: str, url: str) -> str:
        suffix = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
        return f"{slugify(title) or 'news'}-{suffix}"


def rss_item_asof(item: RssNewsItem) -> date:
    if item.published_at:
        return item.published_at.date()
    return date.today()
