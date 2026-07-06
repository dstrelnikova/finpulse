from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.base import SessionLocal
from app.infrastructure.database.models import NewsCacheModel


@dataclass
class CachedSummaryRow:
    cache_date: date
    market: str
    category: str
    url: str
    source: str
    title: str
    payload_json: str


class NewsCacheRepoSQL:
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self._session_factory = session_factory

    def get(self, cache_date: date, category: str, url: str) -> Optional[CachedSummaryRow]:
        with self._session_factory() as session:
            row = session.query(NewsCacheModel).filter_by(cache_date=cache_date, category=category, url=url).first()
            if not row:
                return None
            return CachedSummaryRow(
                cache_date=row.cache_date,
                market=row.market,
                category=row.category,
                url=row.url,
                source=row.source,
                title=row.title,
                payload_json=row.payload_json,
            )

    def upsert(
        self,
        cache_date: date,
        market: str,
        category: str,
        url: str,
        source: str,
        title: str,
        payload_json: str,
    ) -> CachedSummaryRow:
        with self._session_factory() as session:
            row = session.query(NewsCacheModel).filter_by(cache_date=cache_date, category=category, url=url).first()

            if row:
                row.market = market
                row.source = source
                row.title = title
                row.payload_json = payload_json
            else:
                row = NewsCacheModel(
                    cache_date=cache_date,
                    market=market,
                    category=category,
                    url=url,
                    source=source,
                    title=title,
                    payload_json=payload_json,
                )
                session.add(row)

            session.commit()
            session.refresh(row)

            return CachedSummaryRow(
                cache_date=row.cache_date,
                market=row.market,
                category=row.category,
                url=row.url,
                source=row.source,
                title=row.title,
                payload_json=row.payload_json,
            )
