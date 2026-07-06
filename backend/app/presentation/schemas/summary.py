# app/presentation/schemas/news.py

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel

Impact = Literal["positive", "neutral", "negative"]
Confidence = Literal["low", "medium", "high"]


class NewsIndicatorOut(BaseModel):
    impact: Impact
    confidence: Confidence
    importance: Optional[Confidence] = None
    rationale: List[str]


class NewsBlockOut(BaseModel):
    id: str | int
    slug: str

    title: str
    source: str
    url: str

    summary: str
    bullets: List[str]
    conclusion: Optional[str]
    market_meaning: Optional[str] = None
    affected_segments: List[str] = []
    risks: List[str]

    indicator: Optional[NewsIndicatorOut]
    asof: Optional[date]
