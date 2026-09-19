import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from changeguard.domain.models import ActionType
from changeguard.services.audit import AuditLog


@dataclass(frozen=True)
class Approval:
    token_hash: str
    incident_id: str
    action: ActionType
    target: str
    parameters: dict[str, Any]
    approved_by: str
    expires_at: datetime


class ApprovalService:
    def __init__(self, audit: AuditLog, ttl_seconds: int = 900) -> None:
        self.audit = audit
        self.ttl_seconds = ttl_seconds
        self._approvals: dict[str, Approval] = {}

    def approve(
        self,
        incident_id: str,
        action: ActionType,
        target: str,
        parameters: dict[str, Any],
        actor: str,
    ) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = self._hash(token)
        self._approvals[token_hash] = Approval(
            token_hash=token_hash,
            incident_id=incident_id,
            action=action,
            target=target,
            parameters=parameters,
            approved_by=actor,
            expires_at=datetime.now(UTC) + timedelta(seconds=self.ttl_seconds),
        )
        self.audit.append(
            "remediation.approved",
            actor,
            {"incident_id": incident_id, "action": action, "target": target},
        )
        return token

    def consume(self, token: str, incident_id: str, action: ActionType, target: str) -> Approval:
        approval = self._approvals.pop(self._hash(token), None)
        if approval is None:
            raise PermissionError("Approval token is invalid or already consumed")
        if approval.expires_at < datetime.now(UTC):
            raise PermissionError("Approval token has expired")
        approved_scope = (approval.incident_id, approval.action, approval.target)
        if approved_scope != (incident_id, action, target):
            raise PermissionError("Approval does not match the requested remediation")
        return approval

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
