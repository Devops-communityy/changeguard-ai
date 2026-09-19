from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    AWAITING_APPROVAL = "awaiting_approval"
    REMEDIATING = "remediating"
    RESOLVED = "resolved"


class ActionType(StrEnum):
    ARGO_ROLLBACK = "argo_rollback"
    SCALE_DEPLOYMENT = "scale_deployment"
    RESTART_ROLLOUT = "restart_rollout"


class ChangedFile(BaseModel):
    path: str
    additions: int = 0
    deletions: int = 0
    patch: str = ""


class ChangeContext(BaseModel):
    repository: str
    commit_sha: str
    pull_request: int | None = None
    author: str = "unknown"
    title: str = ""
    files: list[ChangedFile] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    deployment_version: str | None = None
    deployed_at: datetime | None = None


class RiskFactor(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)
    reason: str


class ChangeRisk(BaseModel):
    score: int = Field(ge=0, le=100)
    severity: Severity
    factors: list[RiskFactor]
    affected_services: list[str]
    blast_radius: list[str]
    summary: str


class Signal(BaseModel):
    source: str
    name: str
    value: float | str
    unit: str = ""
    baseline: float | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Evidence(BaseModel):
    source: str
    title: str
    detail: str
    relevance: float = Field(default=1.0, ge=0, le=1)
    uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    service: str
    environment: str = "production"
    severity: Severity
    status: IncidentStatus = IncidentStatus.DETECTED
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    signals: list[Signal] = Field(default_factory=list)
    change: ChangeContext | None = None


class RemediationRecommendation(BaseModel):
    action: ActionType
    target: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str
    expected_outcome: str
    risk: Severity
    rollback_plan: str


class InvestigationReport(BaseModel):
    incident_id: UUID
    root_cause: str
    responsible_change: str | None
    confidence: float = Field(ge=0, le=1)
    blast_radius: list[str]
    evidence: list[Evidence]
    similar_incidents: list[Evidence] = Field(default_factory=list)
    recommendations: list[RemediationRecommendation]
    summary: str
