from dataclasses import dataclass, field
from datetime import date
from typing import List, Literal, Optional

Impact = Literal["positive", "neutral", "negative"]
Confidence = Literal["low", "medium", "high"]


@dataclass
class SummaryIndicator:
    impact: Impact
    confidence: Confidence
    rationale: List[str] = field(default_factory=list)


@dataclass
class ArticleSummary:
    id: Optional[int]

    url: str
    source: str
    market: str
    category: str

    asof: date

    bullets: List[str] = field(default_factory=list)
    conclusion: Optional[str] = None
    risks: List[str] = field(default_factory=list)

    summary_text: str = ""

    indicator: Optional[SummaryIndicator] = None
