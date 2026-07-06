from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import MARKET_RU


class UserOut(BaseModel):
    id: int
    name: str
    email: str

    market: Literal["RU"] = MARKET_RU

    investment_horizon: Optional[Literal["short", "mid", "long"]] = None
    experience_level: Optional[Literal["beginner", "intermediate", "pro"]] = None
    risk_level: Optional[Literal["low", "medium", "high"]] = None

    tickers: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
