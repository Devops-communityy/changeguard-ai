from collections.abc import Sequence

import httpx

from changeguard.domain.models import Evidence, Incident


class PrometheusProvider:
    name = "prometheus"

    def __init__(self, base_url: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def collect(self, incident: Incident) -> Sequence[Evidence]:
        service = incident.service.replace('"', "")
        queries = {
            "Request error rate": (
                f'sum(rate(http_requests_total{{service="{service}",status=~"5.."}}[5m])) '
                f'/ clamp_min(sum(rate(http_requests_total{{service="{service}"}}[5m])), 0.001)'
            ),
            "p95 latency": (
                "histogram_quantile(0.95, sum by (le) "
                f'(rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m])))'
            ),
            "Pod CPU": (f'sum(rate(container_cpu_usage_seconds_total{{pod=~"{service}.*"}}[5m]))'),
            "Kafka consumer lag": (f'sum(kafka_consumergroup_lag{{consumergroup="{service}"}})'),
        }
        evidence: list[Evidence] = []
        with httpx.Client(timeout=self.timeout) as client:
            for title, query in queries.items():
                response = client.get(f"{self.base_url}/api/v1/query", params={"query": query})
                response.raise_for_status()
                result = response.json().get("data", {}).get("result", [])
                value = result[0]["value"][1] if result else "no-data"
                evidence.append(
                    Evidence(
                        source=self.name,
                        title=title,
                        detail=f"Current value: {value}",
                        relevance=0.9 if result else 0.2,
                        metadata={"query": query, "series": len(result)},
                    )
                )
        return evidence
