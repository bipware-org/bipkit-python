from __future__ import annotations

from bipkit.types.models import DecisionResponse, EvaluateResponse


def should_escalate(
    response: DecisionResponse | EvaluateResponse,
    *,
    min_confidence_tier: str = "medium",
    max_entropy: float | None = None,
    min_margin: float | None = None,
) -> bool:
    """
    Evaluate whether a System One decision/evaluation should escalate to a System Two LLM.

    Confidence tiers are ordered: ``low`` < ``medium`` < ``high``.
    """
    tier_rank = {"low": 0, "medium": 1, "high": 2}
    required_rank = tier_rank.get(min_confidence_tier.lower(), 1)

    if isinstance(response, DecisionResponse):
        if not response.decisions:
            return True
        top = response.decisions[0]
        if tier_rank.get(top.confidence_tier.lower(), 0) < required_rank:
            return True
        if max_entropy is not None and response.uncertainty_entropy > max_entropy:
            return True
        if min_margin is not None and (top.margin is None or top.margin < min_margin):
            return True
        return False

    # EvaluateResponse: escalate if any result falls below threshold
    if not response.results:
        return True
    for item in response.results.values():
        if not isinstance(item, dict):
            continue
        tier = str(item.get("confidence_tier", "")).lower()
        if tier and tier_rank.get(tier, 0) < required_rank:
            return True
        if max_entropy is not None and "uncertainty_entropy" in item:
            if float(item["uncertainty_entropy"]) > max_entropy:
                return True
        if min_margin is not None and "margin" in item and item["margin"] is not None:
            if float(item["margin"]) < min_margin:
                return True
    return False
