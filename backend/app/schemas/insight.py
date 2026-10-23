from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class ClaimOrigin(str, Enum):
    FACT = "fact"
    BANK_ANALYTICS = "bank_analytics"
    AI_INFERENCE = "ai_inference"
    CLIENT_FEATURE = "client_feature"


class SourceRef(BaseModel):
    source_id: str
    kind: Literal["news", "bank_analytics", "client_data"]
    title: str
    url: str | None = None
    published_at: str | None = None
    excerpt: str | None = None


class Claim(BaseModel):
    text: str
    origin: ClaimOrigin
    source_ids: list[str] = Field(default_factory=list)


class RiskOpportunity(BaseModel):
    kind: Literal["risk", "opportunity"]
    text: str
    severity: Literal["low", "medium", "high"] = "medium"
    origin: ClaimOrigin
    source_ids: list[str] = Field(default_factory=list)


class ClientFeatureUsed(BaseModel):
    name: str
    value: str
    why_matters: str


class Insight(BaseModel):
    insight_id: str
    client_id: str
    event_id: str
    title: str
    what_happened: list[Claim]
    why_it_matters: list[Claim]
    consequences: list[RiskOpportunity]
    actions: list[Claim]
    bank_view: list[Claim]
    based_on: list[SourceRef]
    client_features_used: list[ClientFeatureUsed]
    relevance_score: float
    created_at: str
    trace_id: str


class FollowUpRequest(BaseModel):
    question: str


class FollowUpAnswer(BaseModel):
    insight_id: str
    question: str
    answer: str
    source_ids: list[str] = Field(default_factory=list)