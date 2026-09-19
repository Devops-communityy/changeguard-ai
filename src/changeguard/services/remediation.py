from typing import Any, Protocol

from changeguard.domain.models import ActionType
from changeguard.services.approval import ApprovalService
from changeguard.services.audit import AuditLog


class KubernetesActions(Protocol):
    def scale(self, deployment: str, replicas: int) -> dict[str, object]: ...

    def restart(self, deployment: str) -> dict[str, str]: ...


class ArgoActions(Protocol):
    def rollback(self, application: str, revision_id: int) -> dict[str, object]: ...


class RemediationService:
    def __init__(
        self,
        approvals: ApprovalService,
        audit: AuditLog,
        kubernetes: KubernetesActions | None = None,
        argocd: ArgoActions | None = None,
        dry_run: bool = True,
    ) -> None:
        self.approvals = approvals
        self.audit = audit
        self.kubernetes = kubernetes
        self.argocd = argocd
        self.dry_run = dry_run

    def execute(
        self, token: str, incident_id: str, action: ActionType, target: str, actor: str
    ) -> dict[str, Any]:
        approval = self.approvals.consume(token, incident_id, action, target)
        if self.dry_run:
            result: dict[str, Any] = {
                "status": "dry-run",
                "action": action,
                "target": target,
                "parameters": approval.parameters,
            }
        elif action == ActionType.ARGO_ROLLBACK and self.argocd:
            result = self.argocd.rollback(target, int(approval.parameters["revision_id"]))
        elif action == ActionType.SCALE_DEPLOYMENT and self.kubernetes:
            result = self.kubernetes.scale(target, int(approval.parameters["replicas"]))
        elif action == ActionType.RESTART_ROLLOUT and self.kubernetes:
            result = self.kubernetes.restart(target)
        else:
            raise RuntimeError(f"No executor configured for {action}")
        self.audit.append(
            "remediation.executed",
            actor,
            {"incident_id": incident_id, "approved_by": approval.approved_by, "result": result},
        )
        return result
