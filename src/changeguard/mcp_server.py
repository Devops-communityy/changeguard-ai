from mcp.server.fastmcp import FastMCP

from changeguard.adapters.demo import DemoEvidenceProvider
from changeguard.domain.models import Incident, Severity

mcp = FastMCP("ChangeGuard Production Intelligence")


@mcp.tool()
def inspect_demo_incident(service: str = "telemetry-processing") -> list[dict[str, object]]:
    """Read evidence for the safe local incident simulation."""
    incident = Incident(
        title="Production degradation",
        service=service,
        severity=Severity.HIGH,
    )
    return [item.model_dump(mode="json") for item in DemoEvidenceProvider().collect(incident)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
