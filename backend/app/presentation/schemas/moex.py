from typing import List, Optional

from pydantic import BaseModel


class MoexQuoteOut(BaseModel):
    ticker: str
    short_name: Optional[str] = None
    last: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    update_time: Optional[str] = None
    currency: str = "RUB"


class MoexQuotesResponse(BaseModel):
    index: str
    source: str
    fetched_at: str
    fallback: bool = False
    items: List[MoexQuoteOut]
