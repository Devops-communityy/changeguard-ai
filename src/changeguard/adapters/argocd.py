from collections.abc import Sequence

import httpx

from changeguard.domain.models import Evidence, Incident


class ArgoCDAdapter:
    name = "argocd"

    def __init__(self, base_url: str, token: str, verify_tls: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}
        self.verify_tls = verify_tls

    def collect(self, incident: Incident) -> Sequence[Evidence]:
        with httpx.Client(headers=self.headers, verify=self.verify_tls, timeout=8.0) as client:
            response = client.get(f"{self.base_url}/api/v1/applications/{incident.service}")
            response.raise_for_status()
            app = response.json()
        status = app.get("status", {})
        sync = status.get("sync", {})
        health = status.get("health", {})
        return [
            Evidence(
                source=self.name,
                title="Argo CD application state",
                detail=(
                    f"sync={sync.get('status')}, health={health.get('status')}, "
                    f"revision={sync.get('revision')}"
                ),
                relevance=0.95,
                metadata={"sync": sync, "health": health},
            )
        ]

    def rollback(self, application: str, revision_id: int) -> dict[str, object]:
        if revision_id < 0:
            raise ValueError("Argo CD history revision must be non-negative")
        with httpx.Client(headers=self.headers, verify=self.verify_tls, timeout=15.0) as client:
            response = client.post(
                f"{self.base_url}/api/v1/applications/{application}/rollback",
                json={"id": revision_id},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Argo CD returned a non-object rollback response")
            return payload
