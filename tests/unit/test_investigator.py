from collections.abc import Sequence

from changeguard.adapters import DemoEvidenceProvider
from changeguard.demo import telemetry_incident
from changeguard.domain.models import Evidence, Incident
from changeguard.intelligence.investigator import Investigator


class BrokenProvider:
    name = "broken-provider"

    def collect(self, incident: Incident) -> Sequence[Evidence]:
        raise TimeoutError("upstream timeout")


def test_investigator_isolates_provider_failure() -> None:
    report = Investigator([BrokenProvider(), DemoEvidenceProvider()]).investigate(
        telemetry_incident()
    )

    unavailable = [item for item in report.evidence if item.source == "broken-provider"]
    assert len(unavailable) == 1
    assert unavailable[0].relevance == 0
    assert "TimeoutError" in unavailable[0].detail
    assert report.confidence > 0.8
