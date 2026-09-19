from contextlib import suppress
from typing import Annotated, Any, cast

from fastapi import FastAPI, Header, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, SecretStr

from changeguard.adapters import DemoEvidenceProvider
from changeguard.adapters.argocd import ArgoCDAdapter
from changeguard.adapters.kubernetes import KubernetesAdapter
from changeguard.adapters.prometheus import PrometheusProvider
from changeguard.config import get_settings
from changeguard.domain.models import (
    ActionType,
    ChangeContext,
    ChangeRisk,
    Incident,
    InvestigationReport,
)
from changeguard.domain.risk import ChangeRiskEngine
from changeguard.intelligence.investigator import Investigator
from changeguard.services.approval import ApprovalService
from changeguard.services.audit import AuditLog
from changeguard.services.remediation import RemediationService


class InvestigationRequest(BaseModel):
    incident: Incident
    openai_api_key: SecretStr | None = None


class ApprovalRequest(BaseModel):
    incident_id: str
    action: ActionType
    target: str
    parameters: dict[str, Any]


class ExecutionRequest(BaseModel):
    token: SecretStr
    incident_id: str
    action: ActionType
    target: str


settings = get_settings()
audit = AuditLog(settings.audit_path)
approvals = ApprovalService(audit, settings.approval_ttl_seconds)


def build_remediation_service() -> RemediationService:
    if settings.demo_mode:
        return RemediationService(approvals, audit, dry_run=True)
    kubernetes = KubernetesAdapter(settings.kubernetes_namespace, settings.kubernetes_context)
    argocd = None
    if settings.argocd_token:
        argocd = ArgoCDAdapter(
            settings.argocd_url,
            settings.argocd_token.get_secret_value(),
            settings.argocd_verify_tls,
        )
    return RemediationService(approvals, audit, kubernetes=kubernetes, argocd=argocd, dry_run=False)


def evidence_providers() -> list[Any]:
    if settings.demo_mode:
        return [DemoEvidenceProvider()]
    providers: list[Any] = [PrometheusProvider(settings.prometheus_url)]
    with suppress(Exception):
        providers.append(
            KubernetesAdapter(settings.kubernetes_namespace, settings.kubernetes_context)
        )
    if settings.argocd_token:
        providers.append(
            ArgoCDAdapter(
                settings.argocd_url,
                settings.argocd_token.get_secret_value(),
                settings.argocd_verify_tls,
            )
        )
    return providers


remediation = build_remediation_service()
request_count = Counter(
    "changeguard_http_requests_total", "HTTP requests", ["method", "route", "status"]
)
request_duration = Histogram(
    "changeguard_http_request_duration_seconds", "HTTP request duration", ["method", "route"]
)
app = FastAPI(
    title="ChangeGuard API",
    version="0.1.0",
    description="Production change intelligence with approval-gated remediation",
)


@app.middleware("http")
async def observe_request(request: Request, call_next: Any) -> Response:
    with request_duration.labels(request.method, request.url.path).time():
        response = cast(Response, await call_next(request))
    route = getattr(request.scope.get("route"), "path", request.url.path)
    request_count.labels(request.method, route, response.status_code).inc()
    return response


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/changes/risk", response_model=ChangeRisk)
def analyze_change(change: ChangeContext) -> ChangeRisk:
    return ChangeRiskEngine().analyze(change)


@app.post("/v1/incidents/investigate", response_model=InvestigationReport)
def investigate(request: InvestigationRequest) -> InvestigationReport:
    ui_key = request.openai_api_key.get_secret_value() if request.openai_api_key else None
    configured_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    investigator = Investigator(
        evidence_providers(),
        api_key=ui_key or configured_key,
        model=settings.llm_model,
    )
    try:
        return investigator.investigate(request.incident)
    except Exception as error:
        raise HTTPException(status_code=502, detail="Investigation provider failed") from error


@app.post("/v1/remediations/approve")
def approve(
    request: ApprovalRequest,
    actor: Annotated[str, Header(alias="X-Actor")],
) -> dict[str, str]:
    token = approvals.approve(
        request.incident_id,
        request.action,
        request.target,
        request.parameters,
        actor,
    )
    return {"approval_token": token, "expires_in": str(settings.approval_ttl_seconds)}


@app.post("/v1/remediations/execute")
def execute(
    request: ExecutionRequest,
    actor: Annotated[str, Header(alias="X-Actor")],
) -> dict[str, Any]:
    try:
        return remediation.execute(
            request.token.get_secret_value(),
            request.incident_id,
            request.action,
            request.target,
            actor,
        )
    except (PermissionError, ValueError) as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
