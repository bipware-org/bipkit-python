from __future__ import annotations

import httpx
import pytest

from bipkit import Bipkit
from bipkit.integrations.langchain import (
    BipkitClassifier,
    BipkitGuardrailMiddleware,
    BipkitModelRouterMiddleware,
    ModelChoice,
)


def _langchain_handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/api/v1/evaluate"
    return httpx.Response(
        200,
        json={
            "request_id": "req_lc_1",
            "state": "rm -rf /",
            "engine": "bip-instant",
            "usage": {
                "evaluations_count": 1,
                "state_tokens": 3,
                "evaluation_tokens": 5,
                "total_tokens": 8,
                "latency_ms": 0.5,
            },
            "results": {
                "model_tier": {
                    "type": "choice",
                    "top_choice": "fast",
                    "uncertainty_entropy": 0.1,
                    "decisions": [{"candidate_id": "fast", "margin": 0.8}],
                },
                "is_dangerous": {
                    "type": "noul",
                    "noul": 0.95,
                    "confidence_tier": "high",
                    "confidence_index": 0.98,
                    "margin": 0.9,
                },
            },
        },
    )


def test_router_and_guardrail_middleware() -> None:
    client = Bipkit(
        api_key="bpk_live_test",
        http_client=httpx.Client(transport=httpx.MockTransport(_langchain_handler)),
    )
    classifier = BipkitClassifier(client=client)

    router = BipkitModelRouterMiddleware(
        choices={
            "fast": ModelChoice(model="gpt-4o-mini", criteria="Simple tasks"),
            "deep": ModelChoice(model="o3", criteria="Complex reasoning"),
        },
        classifier=classifier,
    )
    assert router.route("Summarize this sentence") == "gpt-4o-mini"

    guardrail = BipkitGuardrailMiddleware(classifier=classifier, threshold=0.7)
    res = guardrail.inspect("bash", "rm -rf /")
    assert res["is_blocked"] is True
    assert res["risk_prob"] == pytest.approx(0.95)

    safe_tool = guardrail.wrap_tool(lambda cmd: f"ran {cmd}", "bash")
    with pytest.raises(PermissionError):
        safe_tool("rm -rf /")

    exempt = guardrail.inspect("calculator", "2+2")
    assert exempt["is_blocked"] is False
    assert exempt["reason"] == "tool_exempt"
