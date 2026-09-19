from pathlib import PurePosixPath

from changeguard.domain.models import ChangeContext, ChangeRisk, RiskFactor, Severity


class ChangeRiskEngine:
    """Explainable pre-deployment risk scoring independent of an LLM."""

    critical_markers = {
        "deployment",
        "helm",
        "k8s",
        "kubernetes",
        "terraform",
        "schema",
        "migration",
        "consumer",
        "telemetry",
    }
    sensitive_content = {
        "timeout",
        "replicas",
        "memory",
        "cpu",
        "partition",
        "offset",
        "database_url",
        "max.poll",
    }

    def analyze(self, change: ChangeContext) -> ChangeRisk:
        factors: list[RiskFactor] = []
        changed_lines = sum(item.additions + item.deletions for item in change.files)
        file_names = " ".join(item.path.lower() for item in change.files)
        patches = " ".join(item.patch.lower() for item in change.files)

        if changed_lines >= 500:
            factors.append(RiskFactor(name="change_size", score=25, reason="500+ lines changed"))
        elif changed_lines >= 150:
            factors.append(RiskFactor(name="change_size", score=15, reason="150+ lines changed"))
        elif changed_lines >= 50:
            factors.append(RiskFactor(name="change_size", score=8, reason="50+ lines changed"))

        critical_hits = sorted(marker for marker in self.critical_markers if marker in file_names)
        if critical_hits:
            factors.append(
                RiskFactor(
                    name="critical_surface",
                    score=min(30, 12 + 4 * len(critical_hits)),
                    reason=f"Critical production surfaces changed: {', '.join(critical_hits)}",
                )
            )

        content_hits = sorted(marker for marker in self.sensitive_content if marker in patches)
        if content_hits:
            factors.append(
                RiskFactor(
                    name="runtime_behavior",
                    score=min(30, 10 + 4 * len(content_hits)),
                    reason=f"Runtime-sensitive settings changed: {', '.join(content_hits)}",
                )
            )

        extensions = {PurePosixPath(item.path).suffix for item in change.files}
        if len(change.services) > 1:
            factors.append(
                RiskFactor(
                    name="cross_service",
                    score=min(20, 5 * len(change.services)),
                    reason=f"Change affects {len(change.services)} services",
                )
            )
        if {".sql", ".tf"} & extensions:
            factors.append(
                RiskFactor(
                    name="stateful_change", score=20, reason="Stateful infrastructure changed"
                )
            )
        if not any("test" in item.path.lower() for item in change.files):
            factors.append(RiskFactor(name="test_gap", score=10, reason="No test files changed"))

        score = min(100, sum(factor.score for factor in factors))
        severity = self._severity(score)
        services = change.services or self._infer_services(change)
        blast_radius = self._blast_radius(services)
        return ChangeRisk(
            score=score,
            severity=severity,
            factors=factors,
            affected_services=services,
            blast_radius=blast_radius,
            summary=f"{severity.value.upper()} risk change ({score}/100) affecting "
            f"{', '.join(services) or 'an unknown service'}.",
        )

    @staticmethod
    def _severity(score: int) -> Severity:
        if score >= 80:
            return Severity.CRITICAL
        if score >= 60:
            return Severity.HIGH
        if score >= 30:
            return Severity.MEDIUM
        return Severity.LOW

    @staticmethod
    def _infer_services(change: ChangeContext) -> list[str]:
        candidates = {
            parts[1]
            for item in change.files
            if len(parts := PurePosixPath(item.path).parts) > 2 and parts[0] in {"services", "apps"}
        }
        return sorted(candidates)

    @staticmethod
    def _blast_radius(services: list[str]) -> list[str]:
        dependencies = {
            "telemetry-processing": ["vehicle-data-ingestion", "kafka", "analytics", "alerts"],
            "vehicle-data-ingestion": ["telemetry-processing", "kafka"],
            "analytics": ["driver-safety", "fleet-dashboard"],
        }
        return sorted(
            {dependency for service in services for dependency in dependencies.get(service, [])}
        )
