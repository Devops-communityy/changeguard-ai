from changeguard.domain.models import ChangeContext, ChangedFile, Severity
from changeguard.domain.risk import ChangeRiskEngine


def test_telemetry_runtime_change_is_high_risk() -> None:
    change = ChangeContext(
        repository="quantum-vector/vehicle-platform",
        commit_sha="abc1234",
        title="Tune telemetry consumer performance",
        services=["telemetry-processing"],
        deployment_version="5.2.1",
        files=[
            ChangedFile(
                path="services/telemetry-processing/consumer.py",
                additions=180,
                deletions=35,
                patch="timeout=30 max.poll.records=2000 memory_limit=256Mi cpu_limit=250m",
            ),
            ChangedFile(
                path="deploy/helm/telemetry-processing/values.yaml",
                additions=20,
                deletions=12,
                patch="replicas: 2 memory: 256Mi cpu: 250m",
            ),
        ],
    )

    result = ChangeRiskEngine().analyze(change)

    assert result.score >= 60
    assert result.severity in {Severity.HIGH, Severity.CRITICAL}
    assert "kafka" in result.blast_radius
    assert {factor.name for factor in result.factors} >= {
        "change_size",
        "critical_surface",
        "runtime_behavior",
        "test_gap",
    }


def test_small_tested_change_is_low_risk() -> None:
    change = ChangeContext(
        repository="quantum-vector/vehicle-platform",
        commit_sha="def5678",
        services=["fleet-dashboard"],
        files=[
            ChangedFile(path="services/fleet-dashboard/format.py", additions=4, deletions=2),
            ChangedFile(path="tests/test_format.py", additions=8),
        ],
    )

    result = ChangeRiskEngine().analyze(change)

    assert result.severity == Severity.LOW
    assert result.score == 0
