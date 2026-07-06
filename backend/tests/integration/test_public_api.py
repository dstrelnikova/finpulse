import pytest


@pytest.mark.integration
def test_meta_options_available(client):
    res = client.get("/meta/options")
    assert res.status_code == 200
    body = res.json()
    assert "markets" in body
    assert "risk_levels" in body


@pytest.mark.integration
def test_public_moex_limit_is_clamped(client, fake_moex_service):
    res = client.get("/public/moex/imoex/quotes?limit=999")
    assert res.status_code == 200
    assert fake_moex_service.called_limit == 20
    assert len(res.json()["items"]) == 20


@pytest.mark.integration
def test_public_news_endpoints(client):
    feed = client.get("/public/news?limit=10")
    assert feed.status_code == 200
    assert len(feed.json()) == 1

    item = client.get("/public/news/1")
    assert item.status_code == 200
    assert item.json()["slug"] == "market-brief"

    by_slug = client.get("/public/news/slug/market-brief")
    assert by_slug.status_code == 200

    miss = client.get("/public/news/404")
    assert miss.status_code == 404
