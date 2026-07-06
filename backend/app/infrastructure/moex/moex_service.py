from __future__ import annotations

from datetime import datetime, timezone
import threading
import time
from typing import Any, Dict, List

import requests

from app.core.constants import IMOEX_SAMPLE_TICKERS
from app.presentation.schemas.moex import MoexQuoteOut, MoexQuotesResponse


class MoexService:
    def __init__(self, base_url: str = "https://iss.moex.com/iss"):
        self.base_url = base_url.rstrip("/")
        self._last_call_ts = 0.0
        self._rate_lock = threading.Lock()

    def get_imoex_quotes(self, limit: int = 12) -> MoexQuotesResponse:
        tickers = IMOEX_SAMPLE_TICKERS[: max(1, min(limit, len(IMOEX_SAMPLE_TICKERS)))]
        fetched_at = datetime.now(timezone.utc).isoformat()

        try:
            rows = self._fetch_quotes_rows(tickers=tickers)
            return MoexQuotesResponse(
                index="IMOEX",
                source="MOEX ISS",
                fetched_at=fetched_at,
                fallback=False,
                items=rows,
            )
        except Exception:
            fallback_rows = [MoexQuoteOut(ticker=t, short_name=t) for t in tickers]
            return MoexQuotesResponse(
                index="IMOEX",
                source="MOEX ISS (fallback)",
                fetched_at=fetched_at,
                fallback=True,
                items=fallback_rows,
            )

    def _fetch_quotes_rows(self, tickers: List[str]) -> List[MoexQuoteOut]:
        self._rate_limit_wait()

        sec_csv = ",".join(tickers)
        url = (
            f"{self.base_url}/engines/stock/markets/shares/boards/TQBR/securities.json"
            f"?iss.meta=off&iss.only=securities,marketdata"
            f"&securities.columns=SECID,SHORTNAME"
            f"&marketdata.columns=SECID,LAST,CHANGE,LASTTOPREVPRICE,UPDATETIME"
            f"&securities={sec_csv}"
        )

        payload = self._get_json_with_retries(url=url, retries=2)
        securities = self._rows_to_dict(payload.get("securities") or {})
        marketdata = self._rows_to_dict(payload.get("marketdata") or {})

        merged: Dict[str, Dict[str, Any]] = {}
        for secid, sec in securities.items():
            merged[secid] = {"secid": secid, **sec}
        for secid, md in marketdata.items():
            merged.setdefault(secid, {"secid": secid})
            merged[secid].update(md)

        out: List[MoexQuoteOut] = []
        for t in tickers:
            row = merged.get(t, {})
            last = self._to_float(row.get("LAST"))
            change = self._to_float(row.get("CHANGE"))
            change_percent = self._to_float(row.get("LASTTOPREVPRICE"))
            out.append(
                MoexQuoteOut(
                    ticker=t,
                    short_name=self._to_str(row.get("SHORTNAME")),
                    last=last,
                    change=change,
                    change_percent=(
                        change_percent if change_percent is not None else self._calc_change_percent(last, change)
                    ),
                    update_time=self._to_str(row.get("UPDATETIME")),
                )
            )
        return out

    def _get_json_with_retries(self, url: str, retries: int = 2) -> Dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                r = requests.get(url, timeout=8, headers={"User-Agent": "FinPulse/1.0"})
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_error = e
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
        assert last_error is not None
        raise last_error

    def _rate_limit_wait(self) -> None:
        # Простое ограничение частоты: не чаще 5 req/sec
        with self._rate_lock:
            now = time.monotonic()
            min_interval = 0.2
            sleep_for = min_interval - (now - self._last_call_ts)
            if sleep_for > 0:
                time.sleep(sleep_for)
            self._last_call_ts = time.monotonic()

    @staticmethod
    def _rows_to_dict(block: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        columns = block.get("columns") or []
        data = block.get("data") or []
        out: Dict[str, Dict[str, Any]] = {}
        for row in data:
            item = {columns[i]: row[i] for i in range(min(len(columns), len(row)))}
            secid = str(item.get("SECID") or "").strip()
            if secid:
                out[secid] = item
        return out

    @staticmethod
    def _to_float(v: Any) -> float | None:
        try:
            return float(v) if v is not None else None
        except Exception:
            return None

    @staticmethod
    def _calc_change_percent(last: float | None, change: float | None) -> float | None:
        if last is None or change is None:
            return None
        previous = last - change
        if previous == 0:
            return None
        return (change / previous) * 100

    @staticmethod
    def _to_str(v: Any) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None
