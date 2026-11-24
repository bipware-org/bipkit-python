from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _BipkitModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class CandidateModel(_BipkitModel):
    id: str
    label: str | None = None
    description: str | None = None


class UsageModel(_BipkitModel):
    evaluations_count: int
    state_tokens: int
    evaluation_tokens: int
    total_tokens: int
    latency_ms: float = 0.0


class EvaluateRequest(_BipkitModel):
    state: str
    evaluations: dict[str, Any]
    engine: str = "bip-instant"
    temperature: float | None = None


class EvaluateResponse(_BipkitModel):
    request_id: str
    state: str
    engine: str
    usage: UsageModel
    results: dict[str, Any]


class DecisionRequest(_BipkitModel):
    state: str
    choices: list[CandidateModel | dict[str, Any] | str]
    engine: str = "bip-instant"
    top_k: int | None = None
    temperature: float | None = None


class DecisionItemModel(_BipkitModel):
    candidate_id: str
    probability: float
    confidence_tier: str
    confidence_index: float
    margin: float | None = None


class DecisionResponse(_BipkitModel):
    request_id: str
    state: str
    engine: str
    uncertainty_entropy: float
    top_choice: str | None = None
    decisions: list[DecisionItemModel] = Field(default_factory=list)


class CustomerFeedbackRequest(_BipkitModel):
    request_id: str
    verified_decision: Any
    was_accurate: bool
    operator_notes: str | None = None


class CustomerFeedbackResponse(_BipkitModel):
    status: str = "recorded"
    request_id: str
    recorded_at: str


class EngineStatusModel(_BipkitModel):
    name: str
    tier: str
    description: str
    enabled: bool = True
    status: str = "ready"
    is_trained: bool | None = None
    classes: list[str] | None = None


class APIKeyInfo(_BipkitModel):
    id: str
    name: str
    key_prefix: str
    environment: str
    scopes: list[str]
    is_active: bool
    last_used_at: str | None = None
    expires_at: str | None = None
    created_at: str


class CreateAPIKeyRequest(_BipkitModel):
    name: str
    environment: str = "live"
    scopes: list[str] = Field(default_factory=lambda: ["evaluate:run"])


class CreateAPIKeyResponse(_BipkitModel):
    id: str
    name: str
    key: str
    key_prefix: str
    environment: str
    scopes: list[str]
    created_at: str


class RotateAPIKeyRequest(_BipkitModel):
    grace_period_minutes: int = 0


class RotateAPIKeyResponse(_BipkitModel):
    new_key: CreateAPIKeyResponse
    rotated_key_id: str
    previous_key_revoked_immediately: bool
    previous_key_expires_at: str | None = None


class UsageEngineBreakdown(_BipkitModel):
    engine: str
    decisions: int = 0
    evaluations: int = 0
    tokens: int = 0


class UsageSummaryResponse(_BipkitModel):
    organization_id: str
    period_ym: str
    plan_slug: str
    plan_name: str
    subscription_status: str
    decisions_used: int
    evaluations_used: int
    total_tokens: int
    monthly_limit: int
    remaining_quota: int
    avg_latency_ms: float
    by_engine: list[UsageEngineBreakdown] = Field(default_factory=list)


class UsageTimeseriesPoint(_BipkitModel):
    date: str
    decisions: int = 0
    evaluations: int = 0
    tokens: int = 0
    avg_latency_ms: float = 0.0


class UsageTimeseriesResponse(_BipkitModel):
    organization_id: str
    days: int
    points: list[UsageTimeseriesPoint] = Field(default_factory=list)


class RecordOutcomeRequest(_BipkitModel):
    request_id: str
    output_name: str | None = None
    observed_effect: Any


class BatchRecordOutcomeRequest(_BipkitModel):
    items: list[RecordOutcomeRequest]


class ExportBundleRequest(_BipkitModel):
    request_id: str
    output_name: str | None = None
    presented_state: str | None = None


class DplBundle(_BipkitModel):
    schema_version: str = "dpl-bundle/1"
    record: dict[str, Any]
    state_disclosure: dict[str, Any] | None = None
    outcome: dict[str, Any] | None = None
    manifest: dict[str, Any]
    signature: dict[str, Any] | None = None
