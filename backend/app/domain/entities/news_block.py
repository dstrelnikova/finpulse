# app/domain/entities/news_block.py
from dataclasses import dataclass, field
from datetime import date
from typing import List, Literal, Optional

Impact = Literal["positive", "neutral", "negative"]
Confidence = Literal["low", "medium", "high"]


@dataclass
class NewsIndicator:
    impact: Impact
    confidence: Confidence
    rationale: List[str] = field(default_factory=list)


@dataclass
class NewsBlock:
    id: str
    slug: str

    title: str
    source: str
    url: str
    summary: str
    bullets: List[str]
    conclusion: Optional[str]
    risks: List[str]
    indicator: Optional[NewsIndicator]
    asof: Optional[date]
