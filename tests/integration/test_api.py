from fastapi.testclient import TestClient

from changeguard.api import app
from changeguard.demo import telemetry_incident

client = TestClient(app)


def test_health_and_metrics() -> None:
    assert client.get("/healthz").json() == {"status": "ok"}
    assert "changeguard_http_requests_total" in client.get("/metrics").text


def test_change_risk_endpoint() -> None:
    incident = telemetry_incident()
    response = client.post("/v1/changes/risk", json=incident.change.model_dump(mode="json"))

    assert response.status_code == 200
    assert response.json()["score"] >= 60


def test_approval_and_dry_run_execution() -> None:
    incident = telemetry_incident()
    headers = {"X-Actor": "on-call@example.com"}
    request = {
        "incident_id": str(incident.id),
        "action": "argo_rollback",
        "target": incident.service,
        "parameters": {"revision_id": 4},
    }
    approval = client.post("/v1/remediations/approve", headers=headers, json=request)

    assert approval.status_code == 200
    execution = client.post(
        "/v1/remediations/execute",
        headers=headers,
        json={
            "token": approval.json()["approval_token"],
            "incident_id": request["incident_id"],
            "action": request["action"],
            "target": request["target"],
        },
    )

    assert execution.status_code == 200
    assert execution.json()["status"] == "dry-run"
