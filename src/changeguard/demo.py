from datetime import UTC, datetime, timedelta

from changeguard.domain.models import ChangeContext, ChangedFile, Incident, Severity, Signal


def telemetry_incident() -> Incident:
    deployed_at = datetime.now(UTC) - timedelta(minutes=18)
    change = ChangeContext(
        repository="quantum-vector/autonomous-vehicle-platform",
        commit_sha="9b7f2d1",
        pull_request=418,
        author="vehicle-platform-team",
        title="Optimize telemetry consumer throughput",
        services=["telemetry-processing"],
        deployment_version="5.2.1",
        deployed_at=deployed_at,
        files=[
            ChangedFile(
                path="services/telemetry-processing/consumer.py",
                additions=180,
                deletions=35,
                patch="max.poll.records=2000 timeout=30 memory_limit=256Mi cpu_limit=250m",
            ),
            ChangedFile(
                path="deploy/helm/telemetry-processing/values.yaml",
                additions=20,
                deletions=12,
                patch="replicas: 2 memory: 256Mi cpu: 250m",
            ),
        ],
    )
    return Incident(
        title="Vehicle telemetry processing delay",
        service="telemetry-processing",
        severity=Severity.HIGH,
        detected_at=datetime.now(UTC) - timedelta(minutes=12),
        change=change,
        signals=[
            Signal(source="prometheus", name="p95 latency", value=3.2, unit="s", baseline=0.2),
            Signal(source="kafka", name="consumer lag", value=48200, unit="messages", baseline=120),
            Signal(
                source="kubernetes",
                name="CPU limit utilization",
                value=96,
                unit="%",
                baseline=42,
            ),
            Signal(source="otel", name="error rate", value=8.4, unit="%", baseline=0.3),
        ],
    )
