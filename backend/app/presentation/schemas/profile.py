from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.constants import (
    ALLOWED_EXPERIENCE,
    ALLOWED_HORIZONS,
    ALLOWED_RISK,
    ALLOWED_SECTORS,
    MARKET_RU,
    TICKER_RE,
)


class ProfileUpdate(BaseModel):
    """
    Профиль пользователя FinPulse (MVP):
    - рынок: RU (фиксировано, не редактируется)
    - горизонт инвестирования
    - уровень опыта
    - интересующие акции/сектора
    - уровень риска
    """

    market: Literal["RU"] = Field(default=MARKET_RU)

    investment_horizon: Optional[Literal["short", "mid", "long"]] = None
    experience_level: Optional[Literal["beginner", "intermediate", "pro"]] = None

    tickers: Optional[List[str]] = None
    sectors: Optional[List[str]] = None

    risk_level: Optional[Literal["low", "medium", "high"]] = None

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: Optional[List[str]]):
        if v is None:
            return v

        cleaned = []
        for t in v:
            if not isinstance(t, str):
                raise ValueError("Тикер должен быть строкой")
            t2 = t.strip().upper()
            if not TICKER_RE.match(t2):
                raise ValueError(f"Некорректный тикер: {t}")
            cleaned.append(t2)

        seen = set()
        unique = []
        for t in cleaned:
            if t not in seen:
                seen.add(t)
                unique.append(t)

        return unique

    @field_validator("sectors")
    @classmethod
    def validate_sectors(cls, v: Optional[List[str]]):
        if v is None:
            return v

        cleaned = []
        for s in v:
            if not isinstance(s, str):
                raise ValueError("Сектор должен быть строкой")
            s2 = s.strip().lower()
            if s2 not in ALLOWED_SECTORS:
                raise ValueError(f"Недопустимый сектор: {s}")
            cleaned.append(s2)

        return list(dict.fromkeys(cleaned))

    @field_validator("investment_horizon")
    @classmethod
    def validate_horizon(cls, v):
        if v is None:
            return v
        if v not in ALLOWED_HORIZONS:
            raise ValueError("Недопустимый горизонт инвестирования")
        return v

    @field_validator("experience_level")
    @classmethod
    def validate_experience(cls, v):
        if v is None:
            return v
        if v not in ALLOWED_EXPERIENCE:
            raise ValueError("Недопустимый уровень опыта")
        return v

    @field_validator("risk_level")
    @classmethod
    def validate_risk(cls, v):
        if v is None:
            return v
        if v not in ALLOWED_RISK:
            raise ValueError("Недопустимый уровень риска")
        return v
