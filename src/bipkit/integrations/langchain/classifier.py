from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bipkit.client import Bipkit
from bipkit.types.models import CandidateModel


@dataclass
class NoulItem:
    noul: float
    confidence_tier: str
    confidence_index: float = 0.0
    margin: float | None = None


@dataclass
class ScoreItem:
    level: str
    score: float
    distribution: dict[str, float]
    confidence_tier: str
    confidence_index: float = 0.0


@dataclass
class ChoiceItem:
    top_choice: str | None
    uncertainty_entropy: float
    decisions: list[dict[str, Any]]
    margin: float | None = None


class BipkitResponse:
    """Structured typed response wrapper for LangChain/LangGraph workflows."""

    def __init__(self, raw: Mapping[str, Any]) -> None:
        self.raw = dict(raw)
        self.request_id: str | None = raw.get("request_id")
        self.state: str = str(raw.get("state", ""))
        self.engine: str = str(raw.get("engine", ""))
        self.usage: dict[str, Any] = dict(raw.get("usage", {}))
        self.results: dict[str, Any] = dict(raw.get("results", {}))
        self.answers = self.results

        self.nouls: dict[str, NoulItem] = {}
        self.scores: dict[str, ScoreItem] = {}
        self.choices: dict[str, ChoiceItem] = {}

        for key, value in self.results.items():
            if not isinstance(value, dict):
                continue
            ans_type = value.get("type")
            if ans_type == "noul":
                self.nouls[key] = NoulItem(
                    noul=float(value.get("noul", 0.0)),
                    confidence_tier=str(value.get("confidence_tier", "low")),
                    confidence_index=float(value.get("confidence_index", 0.0)),
                    margin=value.get("margin"),
                )
            elif ans_type == "score":
                self.scores[key] = ScoreItem(
                    level=str(value.get("level", "")),
                    score=float(value.get("score", 0.0)),
                    distribution=dict(value.get("distribution", {})),
                    confidence_tier=str(value.get("confidence_tier", "low")),
                    confidence_index=float(value.get("confidence_index", 0.0)),
                )
            elif ans_type == "choice":
                decisions = list(value.get("decisions", []))
                top_margin = decisions[0].get("margin") if decisions else None
                self.choices[key] = ChoiceItem(
                    top_choice=value.get("top_choice"),
                    uncertainty_entropy=float(value.get("uncertainty_entropy", 0.0)),
                    decisions=decisions,
                    margin=top_margin,
                )


class Noul:
    def __init__(self, instructions: str, negative_instructions: str | None = None) -> None:
        self.type = "noul"
        self.instructions = instructions
        self.negative_instructions = negative_instructions


class Score:
    def __init__(
        self,
        levels: list[str] | None = None,
        instructions: str | None = None,
    ) -> None:
        self.type = "score"
        self.levels = levels or ["low", "medium", "high"]
        self.instructions = instructions


class Choice:
    def __init__(self, choices: list[Any], top_k: int | None = None) -> None:
        self.type = "choice"
        self.choices = choices
        self.top_k = top_k


class BipkitClassifier:
    """
    HTTP-backed LangChain & LangGraph compatible classifier targeting Bipkit Cloud API.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        engine: str = "bip-instant",
        client: Bipkit | None = None,
    ) -> None:
        self.engine = engine
        self._client = client or Bipkit(api_key=api_key, base_url=base_url)

    def invoke(self, payload: Mapping[str, Any]) -> BipkitResponse:
        state = str(payload.get("state", ""))
        evaluations = payload.get("evaluations") or payload.get("questions", {})
        engine_name = str(payload.get("engine", self.engine))

        serialized_eval: dict[str, Any] = {}
        for key, value in evaluations.items():
            if isinstance(value, Noul):
                serialized_eval[key] = {
                    "type": "noul",
                    "instructions": value.instructions,
                    "negative_instructions": value.negative_instructions,
                }
            elif isinstance(value, Score):
                serialized_eval[key] = {
                    "type": "score",
                    "levels": value.levels,
                    "instructions": value.instructions,
                }
            elif isinstance(value, Choice):
                serialized_eval[key] = {
                    "type": "choice",
                    "choices": [
                        c.model_dump(exclude_none=True) if isinstance(c, CandidateModel) else c
                        for c in value.choices
                    ],
                    "top_k": value.top_k,
                }
            elif isinstance(value, Mapping):
                serialized_eval[key] = dict(value)
            else:
                raise ValueError(f"Unsupported evaluation type: {type(value)}")

        res = self._client.evaluate(
            state=state,
            evaluations=serialized_eval,
            engine=engine_name,
        )
        return BipkitResponse(res.model_dump())
