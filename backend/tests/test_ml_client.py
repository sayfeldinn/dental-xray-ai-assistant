"""DentexClient: identity-token auth for a private ML service (Cloud Run). No network."""

import importlib

import httpx

from app.services.ml_client.dentex_client import DentexClient

# The package re-exports an *instance* named dentex_client, which shadows the module name.
module = importlib.import_module("app.services.ml_client.dentex_client")

ML_URL = "https://dentalai-ml-abc.a.run.app"


def _recorder():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/predict":
            return httpx.Response(200, json={"detections": [], "image_width": 10, "image_height": 5})
        return httpx.Response(200, json={"status": "ok"})

    return seen, httpx.MockTransport(handler)


def _fetcher(tokens):
    calls = []

    async def fetch(audience):
        calls.append(audience)
        return tokens[len(calls) - 1]

    return calls, fetch


async def test_no_authorization_header_when_auth_is_off():
    seen, transport = _recorder()
    calls, fetch = _fetcher(["unused"])
    client = DentexClient(base_url="http://ml:8001", auth=False, token_fetcher=fetch, transport=transport)
    await client.analyze_scan(b"img", "x.png", 0.2)
    assert "authorization" not in seen[0].headers
    assert calls == []


async def test_every_call_carries_an_identity_token_for_the_ml_service():
    seen, transport = _recorder()
    calls, fetch = _fetcher(["tok-1"])
    client = DentexClient(base_url=ML_URL, auth=True, token_fetcher=fetch, transport=transport)
    await client.health_check()
    await client.analyze_scan(b"img", "x.png", 0.2)
    await client.submit_feedback("scan", 3, 6, "Caries", False, "Deep Caries")
    assert [r.headers["authorization"] for r in seen] == ["Bearer tok-1"] * 3
    assert calls == [ML_URL]            # audience = the service URL, fetched once and reused


async def test_the_token_is_refreshed_after_it_expires(monkeypatch):
    seen, transport = _recorder()
    calls, fetch = _fetcher(["tok-1", "tok-2"])
    clock = [1000.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    client = DentexClient(base_url=ML_URL, auth=True, token_fetcher=fetch, transport=transport)
    await client.health_check()
    clock[0] += module.TOKEN_LIFETIME_SECONDS + 1
    await client.health_check()
    assert [r.headers["authorization"] for r in seen] == ["Bearer tok-1", "Bearer tok-2"]


async def test_metadata_request_asks_for_the_right_audience(monkeypatch):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, text="id-token\n")

    real = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, "AsyncClient",
                        lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    assert await module.fetch_identity_token(ML_URL) == "id-token"
    assert seen[0].headers["metadata-flavor"] == "Google"
    assert seen[0].url.params["audience"] == ML_URL
