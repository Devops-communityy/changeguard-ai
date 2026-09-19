from collections.abc import Sequence

from changeguard.domain.models import Evidence, Incident


class DemoEvidenceProvider:
    name = "demo-observability"

    def collect(self, incident: Incident) -> Sequence[Evidence]:
        version = incident.change.deployment_version if incident.change else "unknown"
        return [
            Evidence(
                source="prometheus",
                title="Latency regression",
                detail="p95 latency increased from 0.20s to 3.20s immediately after deployment.",
                relevance=0.98,
                metadata={"query": "service_request_duration_seconds:p95", "value": 3.2},
            ),
            Evidence(
                source="kafka",
                title="Consumer lag increasing",
                detail=(
                    "vehicle-telemetry consumer group lag increased from 120 to 48,200 messages."
                ),
                relevance=0.96,
                metadata={"consumer_group": "telemetry-processing", "lag": 48200},
            ),
            Evidence(
                source="kubernetes",
                title="CPU saturation",
                detail="telemetry-processing pods are using 96% of their configured CPU limit.",
                relevance=0.91,
                metadata={"deployment": incident.service, "cpu_ratio": 0.96},
            ),
            Evidence(
                source="argocd",
                title="Recent deployment",
                detail=(
                    f"Argo CD synced {incident.service} version {version} before the regression."
                ),
                relevance=0.94,
                metadata={"version": version, "health": "Degraded"},
            ),
        ]
