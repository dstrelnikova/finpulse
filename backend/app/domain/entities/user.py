from dataclasses import dataclass, field
from typing import List, Literal, Optional

from app.core.constants import MARKET_RU


@dataclass
class User:
    id: int | None
    name: str
    email: str
    password_hash: str

    market: Literal["RU"] = MARKET_RU

    investment_horizon: Optional[str] = None  # "short" | "mid" | "long"
    experience_level: Optional[str] = None  # "beginner" | "intermediate" | "pro"
    risk_level: Optional[str] = None  # "low" | "medium" | "high"

    tickers: List[str] = field(default_factory=list)  # ["SBER", "GAZP", ...]
    sectors: List[str] = field(default_factory=list)  # ["banks", "oil_gas", ...]
