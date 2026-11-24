from __future__ import annotations

import json

import httpx
import pytest

from bipkit import (
    AsyncBipkit,
    AuthenticationError,
    Bipkit,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ValidationError,
    should_escalate,
)


def _mock_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    method = request.method
    if path == "/api/v1/health" and method == "GET":
        return httpx.Response(200, json={"status": "ok"})
    if path == "/api/v1/evaluate" and method == "POST":
        return httpx.Response(
            200,
            json={
                "request_id": "req_eval_1",
                "state": "test state",
                "engine": "bip-instant",
                "usage": {
                    "evaluations_count": 1,
                    "state_tokens": 2,
                    "evaluation_tokens": 4,
                    "total_tokens": 6,
                    "latency_ms": 0.8,
                },
                "results": {
                    "risk": {
                        "type": "noul",
                        "noul": 0.91,
                        "confidence_tier": "high",
                        "confidence_index": 0.95,
                        "margin": 0.42,
                    }
                },
            },
        )
    if path == "/api/v1/decide" and method == "POST":
        return httpx.Response(
            200,
            json={
                "request_id": "req_dec_1",
                "state": "refund please",
                "engine": "bip-cascade",
                "uncertainty_entropy": 0.12,
                "top_choice": "billing",
                "decisions": [
                    {
                        "candidate_id": "billing",
                        "probability": 0.93,
                        "confidence_tier": "high",
                        "confidence_index": 0.96,
                        "margin": 0.86,
                    }
                ],
            },
        )
    if path == "/api/v1/feedback" and method == "POST":
        return httpx.Response(
            200,
            json={
                "status": "recorded",
                "request_id": "req_dec_1",
                "recorded_at": "2026-11-24T12:00:00Z",
            },
        )
    if path == "/api/v1/engines" and method == "GET":
        return httpx.Response(
            200,
            json=[
                {
                    "name": "bip-instant",
                    "tier": "instant",
                    "description": "Sub-ms tier",
                    "enabled": True,
                    "status": "ready",
                }
            ],
        )
    if path == "/api/v1/api-keys" and method == "GET":
        return httpx.Response(
            200,
            json=[
                {
                    "id": "key_1",
                    "name": "prod",
                    "key_prefix": "bpk_live_abc",
                    "environment": "live",
                    "scopes": ["evaluate:run"],
                    "is_active": True,
                    "created_at": "2026-11-24T00:00:00Z",
                }
            ],
        )
    if path == "/api/v1/api-keys" and method == "POST":
        return httpx.Response(
            200,
            json={
                "id": "key_2",
                "name": "ci",
                "key": "bpk_live_secret",
                "key_prefix": "bpk_live_sec",
                "environment": "live",
                "scopes": ["evaluate:run"],
                "created_at": "2026-11-24T00:00:00Z",
            },
        )
    if path == "/api/v1/api-keys/key_2/rotate" and method == "POST":
        return httpx.Response(
            200,
            json={
                "new_key": {
                    "id": "key_3",
                    "name": "ci",
                    "key": "bpk_live_secret2",
                    "key_prefix": "bpk_live_sec2",
                    "environment": "live",
                    "scopes": ["evaluate:run"],
                    "created_at": "2026-11-24T00:00:00Z",
                },
                "rotated_key_id": "key_2",
                "previous_key_revoked_immediately": True,
            },
        )
    if path == "/api/v1/api-keys/key_2" and method == "DELETE":
        return httpx.Response(200, json={"revoked": True})
    if path == "/api/v1/usage/summary" and method == "GET":
        return httpx.Response(
            200,
            json={
                "organization_id": "org_1",
                "period_ym": "2026-11",
                "plan_slug": "enterprise",
                "plan_name": "Enterprise",
                "subscription_status": "active",
                "decisions_used": 100,
                "evaluations_used": 50,
                "total_tokens": 5000,
                "monthly_limit": 1000000,
                "remaining_quota": 999850,
                "avg_latency_ms": 0.9,
                "by_engine": [],
            },
        )
    if path == "/api/v1/usage/timeseries" and method == "GET":
        return httpx.Response(
            200,
            json={"organization_id": "org_1", "days": 7, "points": []},
        )
    if path.startswith("/api/v1/provenance/"):
        return httpx.Response(200, json={"ok": True, "path": path})
    return httpx.Response(404, json={"detail": "Not found"})


def test_sync_all_public_resources() -> None:
    transport = httpx.MockTransport(_mock_handler)
    with Bipkit(
        api_key="bpk_live_test",
        http_client=httpx.Client(transport=transport),
    ) as client:
        assert client.health()["status"] == "ok"
        eval_res = client.evaluate(state="test state", evaluations={"risk": {"type": "noul"}})
        assert eval_res.request_id == "req_eval_1"
        assert not should_escalate(eval_res)

        dec_res = client.decide(state="refund please", choices=[{"id": "billing"}])
        assert dec_res.top_choice == "billing"
        assert not should_escalate(dec_res, min_confidence_tier="high", max_entropy=0.2)
        assert should_escalate(dec_res, max_entropy=0.05)

        fb = client.feedback.submit(
            request_id="req_dec_1",
            verified_decision="billing",
            was_accurate=True,
        )
        assert fb.status == "recorded"
        assert client.engines.list()[0].name == "bip-instant"
        assert len(client.api_keys.list()) == 1
        assert client.api_keys.create(name="ci").key == "bpk_live_secret"
        assert client.api_keys.rotate("key_2").rotated_key_id == "key_2"
        assert client.api_keys.revoke("key_2")["revoked"] is True
        assert client.usage.summary().plan_slug == "enterprise"
        assert client.usage.timeseries(days=7).days == 7

        # All 12 DPL endpoints
        assert client.provenance.manifest()["ok"] is True
        assert client.provenance.calibration()["ok"] is True
        assert client.provenance.keys()["ok"] is True
        assert client.provenance.record_outcome(request_id="r1", observed_effect=True)["ok"] is True
        assert (
            client.provenance.record_outcomes_batch(
                [{"request_id": "r1", "observed_effect": True}]
            )["ok"]
            is True
        )
        assert client.provenance.chain(from_seq=0, limit=10)["ok"] is True
        assert client.provenance.metrics()["ok"] is True
        assert client.provenance.records(limit=5)["ok"] is True
        assert client.provenance.get_record("ent_1")["ok"] is True
        assert client.provenance.get_request("req_1")["ok"] is True
        assert client.provenance.export(request_id="req_1")["ok"] is True
        assert (
            client.provenance.verify({"record": {}, "manifest": {}})["ok"] is True
        )


def test_async_client() -> None:
    import asyncio

    async def _run() -> None:
        transport = httpx.MockTransport(_mock_handler)
        async with AsyncBipkit(
            api_key="bpk_live_test",
            http_client=httpx.AsyncClient(transport=transport),
        ) as client:
            assert (await client.health())["status"] == "ok"
            dec = await client.decide(state="refund please", choices=["billing", "support"])
            assert dec.top_choice == "billing"
            assert (await client.engines.list())[0].name == "bip-instant"

    asyncio.run(_run())


def test_error_mapping_and_retries() -> None:
    attempts = {"count": 0}

    def retry_handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if request.url.path == "/api/v1/engines":
            if attempts["count"] < 2:
                return httpx.Response(429, headers={"Retry-After": "0"}, json={"detail": "Slow down"})
            return httpx.Response(200, json=[])
        status_map = {
            "/api/v1/401": 401,
            "/api/v1/403": 403,
            "/api/v1/404": 404,
            "/api/v1/422": 422,
            "/api/v1/429": 429,
        }
        code = status_map.get(request.url.path, 500)
        return httpx.Response(code, headers={"x-request-id": "req_err"}, json={"detail": f"err {code}"})

    client = Bipkit(
        api_key="bpk_live_test",
        max_retries=2,
        http_client=httpx.Client(transport=httpx.MockTransport(retry_handler)),
    )
    assert client.engines.list() == []
    assert attempts["count"] == 2

    no_retry = Bipkit(
        api_key="bpk_live_test",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(retry_handler)),
    )
    with pytest.raises(AuthenticationError) as e401:
        no_retry._transport.request("GET", "/api/v1/401")
    assert e401.value.request_id == "req_err"

    with pytest.raises(PermissionError):
        no_retry._transport.request("GET", "/api/v1/403")
    with pytest.raises(NotFoundError):
        no_retry._transport.request("GET", "/api/v1/404")
    with pytest.raises(ValidationError):
        no_retry._transport.request("GET", "/api/v1/422")
    with pytest.raises(RateLimitError):
        no_retry._transport.request("GET", "/api/v1/429")


def test_user_agent_and_bearer_header() -> None:
    captured: dict[str, str] = {}

    def inspect_handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization", "")
        captured["ua"] = request.headers.get("user-agent", "")
        body = json.loads(request.content.decode()) if request.content else {}
        return httpx.Response(200, json={"status": "recorded", "request_id": body.get("request_id", "x"), "recorded_at": "2026-11-24T00:00:00Z"})

    client = Bipkit(
        api_key="bpk_live_abc",
        http_client=httpx.Client(transport=httpx.MockTransport(inspect_handler)),
    )
    client.feedback.submit(request_id="r1", verified_decision="ok", was_accurate=True)
    assert captured["auth"] == "Bearer bpk_live_abc"
    assert captured["ua"].startswith("bipkit-python/")
