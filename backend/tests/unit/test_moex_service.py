import pytest

from app.infrastructure.moex.moex_service import MoexService


@pytest.mark.unit
def test_moex_service_returns_fallback_on_fetch_error(monkeypatch):
    svc = MoexService()

    def _boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(svc, "_fetch_quotes_rows", _boom)

    data = svc.get_imoex_quotes(limit=3)

    assert data.fallback is True
    assert len(data.items) == 3
    assert data.source.startswith("MOEX ISS")


@pytest.mark.unit
def test_moex_service_clamps_limit_to_available_tickers(monkeypatch):
    svc = MoexService()

    captured = {}

    def _fake_fetch(tickers):
        captured["tickers"] = tickers
        return []

    monkeypatch.setattr(svc, "_fetch_quotes_rows", _fake_fetch)

    svc.get_imoex_quotes(limit=999)

    assert len(captured["tickers"]) <= 12
    assert len(captured["tickers"]) > 0


@pytest.mark.unit
def test_moex_service_calculates_change_percent_fallback():
    assert MoexService._calc_change_percent(last=105.0, change=5.0) == 5.0
