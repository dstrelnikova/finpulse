import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Set

CATEGORY_MACRO = "macro"
CATEGORY_STOCKS = "stocks"

ALLOWED_CATEGORIES: Set[str] = {CATEGORY_MACRO, CATEGORY_STOCKS}

MARKET_RU: Literal["RU"] = "RU"
ALLOWED_MARKETS: Set[str] = {MARKET_RU}

ALLOWED_HORIZONS: Set[str] = {"short", "mid", "long"}
ALLOWED_EXPERIENCE: Set[str] = {"beginner", "intermediate", "pro"}
ALLOWED_RISK: Set[str] = {"low", "medium", "high"}

ALLOWED_SECTORS: Set[str] = {
    "banks",
    "oil_gas",
    "metals_mining",
    "it",
    "consumer",
    "telecom",
    "utilities",
    "real_estate",
    "transport",
    "industrials",
    "financials_other",
}

TICKER_RE = re.compile(r"^[A-Z0-9\.]{2,12}$")

NEWS_SOURCES: Dict[str, Dict[str, List[str]]] = {
    MARKET_RU: {
        CATEGORY_MACRO: [
            "https://www.cbr.ru/press/",
            "https://minfin.gov.ru/ru/press-center/",
            "https://www.rbc.ru/economics/",
        ],
        CATEGORY_STOCKS: [
            "https://www.moex.com/ru/news/",
            "https://www.rbc.ru/finances/",
            "https://www.interfax.ru/business/",
        ],
    }
}


@dataclass(frozen=True)
class RssNewsSource:
    name: str
    url: str
    category: str
    market: str = MARKET_RU


PUBLIC_RSS_NEWS_SOURCES: List[RssNewsSource] = [
    RssNewsSource(
        name="Банк России",
        url="https://www.cbr.ru/rss/RssPress",
        category=CATEGORY_MACRO,
    ),
    RssNewsSource(
        name="Банк России",
        url="https://www.cbr.ru/rss/eventrss",
        category=CATEGORY_MACRO,
    ),
    RssNewsSource(
        name="Московская биржа",
        url="https://www.moex.com/export/news.aspx?cat=201",
        category=CATEGORY_STOCKS,
    ),
    RssNewsSource(
        name="Московская биржа",
        url="https://www.moex.com/export/news.aspx?cat=206",
        category=CATEGORY_STOCKS,
    ),
    RssNewsSource(
        name="Интерфакс Бизнес",
        url="https://www.interfax.ru/business/",
        category=CATEGORY_STOCKS,
    ),
    RssNewsSource(
        name="Коммерсантъ Финансы",
        url="https://www.kommersant.ru/finance",
        category=CATEGORY_STOCKS,
    ),
]

# Базовый набор ликвидных бумаг (используем как sample-представление состава IMOEX для MVP).
IMOEX_SAMPLE_TICKERS: List[str] = [
    "SBER",
    "GAZP",
    "LKOH",
    "ROSN",
    "NVTK",
    "GMKN",
    "TATN",
    "SNGS",
    "MGNT",
    "YDEX",
    "PLZL",
    "CHMF",
]
