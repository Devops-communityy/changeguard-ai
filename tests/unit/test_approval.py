from pathlib import Path

import pytest

from changeguard.domain.models import ActionType
from changeguard.services.approval import ApprovalService
from changeguard.services.audit import AuditLog


def test_approval_is_bound_and_single_use(tmp_path: Path) -> None:
    service = ApprovalService(AuditLog(tmp_path / "audit.jsonl"))
    token = service.approve(
        incident_id="inc-1",
        action=ActionType.ARGO_ROLLBACK,
        target="telemetry-processing",
        parameters={"revision": 4},
        actor="on-call@example.com",
    )

    approval = service.consume(token, "inc-1", ActionType.ARGO_ROLLBACK, "telemetry-processing")

    assert approval.approved_by == "on-call@example.com"
    with pytest.raises(PermissionError, match="invalid or already consumed"):
        service.consume(token, "inc-1", ActionType.ARGO_ROLLBACK, "telemetry-processing")
