from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from bipkit.integrations.langchain.classifier import BipkitClassifier, Choice, Noul
from bipkit.types.models import CandidateModel


@dataclass
class ModelChoice:
    model: str
    criteria: str


class BipkitModelRouterMiddleware:
    """Routes incoming requests to the most cost-effective LLM tier via Bipkit."""

    def __init__(
        self,
        choices: dict[str, ModelChoice],
        *,
        instructions: str = "Choose the least costly model that can complete the task.",
        classifier: BipkitClassifier | None = None,
    ) -> None:
        self.choices = choices
        self.instructions = instructions
        self.classifier = classifier or BipkitClassifier()
        self._candidates = [
            CandidateModel(
                id=tier_name,
                label=tier_name,
                description=f"{mc.criteria} (Model: {mc.model})",
            )
            for tier_name, mc in self.choices.items()
        ]

    def route(self, state: str) -> str:
        resp = self.classifier.invoke(
            {
                "state": state,
                "evaluations": {"model_tier": Choice(choices=self._candidates, top_k=1)},
            }
        )
        choice_item = resp.choices.get("model_tier")
        if choice_item and choice_item.top_choice and choice_item.top_choice in self.choices:
            return self.choices[choice_item.top_choice].model
        first_key = next(iter(self.choices.keys()))
        return self.choices[first_key].model


class BipkitGuardrailMiddleware:
    """Pre-execution safety guardrail for agent tool calls."""

    def __init__(
        self,
        *,
        tools: list[str] | None = None,
        danger_instructions: str = (
            "The command or action causes destructive data loss, irreversible system "
            "modification, or severe security hazard"
        ),
        threshold: float = 0.70,
        classifier: BipkitClassifier | None = None,
    ) -> None:
        self.tools = tools or ["bash", "sh", "terminal", "sql"]
        self.danger_instructions = danger_instructions
        self.threshold = threshold
        self.classifier = classifier or BipkitClassifier()

    def inspect(self, tool_name: str, tool_input: Any) -> dict[str, Any]:
        if tool_name not in self.tools:
            return {
                "tool": tool_name,
                "is_blocked": False,
                "risk_prob": 0.0,
                "reason": "tool_exempt",
            }

        state_text = f"Tool: {tool_name}\nInput: {tool_input}"
        resp = self.classifier.invoke(
            {
                "state": state_text,
                "evaluations": {"is_dangerous": Noul(instructions=self.danger_instructions)},
            }
        )
        noul_item = resp.nouls["is_dangerous"]
        is_blocked = noul_item.noul >= self.threshold
        return {
            "tool": tool_name,
            "is_blocked": is_blocked,
            "risk_prob": noul_item.noul,
            "confidence_tier": noul_item.confidence_tier,
            "reason": "danger_threshold_exceeded" if is_blocked else "safe",
        }

    def wrap_tool(self, tool_fn: Callable[..., Any], tool_name: str) -> Callable[..., Any]:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            inspection = self.inspect(tool_name, kwargs or args)
            if inspection["is_blocked"]:
                raise PermissionError(
                    f"BipkitGuardrail blocked execution of '{tool_name}'! "
                    f"Risk probability ({inspection['risk_prob']:.2f}) exceeded threshold ({self.threshold:.2f})."
                )
            return tool_fn(*args, **kwargs)

        return wrapped
