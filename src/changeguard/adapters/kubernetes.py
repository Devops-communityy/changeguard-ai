from collections.abc import Sequence
from datetime import UTC, datetime

from kubernetes import client, config

from changeguard.domain.models import Evidence, Incident


class KubernetesAdapter:
    name = "kubernetes"

    def __init__(self, namespace: str, context: str | None = None) -> None:
        self.namespace = namespace
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config(context=context)
        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()

    def collect(self, incident: Incident) -> Sequence[Evidence]:
        selector = f"app.kubernetes.io/name={incident.service}"
        pods = self.core.list_namespaced_pod(self.namespace, label_selector=selector).items
        evidence: list[Evidence] = []
        for pod in pods:
            statuses = pod.status.container_statuses or []
            restarts = sum(status.restart_count for status in statuses)
            waiting = [
                status.state.waiting.reason
                for status in statuses
                if status.state and status.state.waiting
            ]
            evidence.append(
                Evidence(
                    source=self.name,
                    title=f"Pod {pod.metadata.name}",
                    detail=(
                        f"phase={pod.status.phase}, restarts={restarts}, "
                        f"waiting={','.join(waiting) or 'none'}"
                    ),
                    relevance=0.95 if restarts or waiting else 0.6,
                    metadata={"pod": pod.metadata.name, "restarts": restarts},
                )
            )
        events = self.core.list_namespaced_event(
            self.namespace, field_selector="involvedObject.kind=Deployment"
        ).items
        oldest = datetime.min.replace(tzinfo=UTC)
        recent_events = sorted(events, key=lambda item: item.last_timestamp or oldest)[-10:]
        for event in recent_events:
            if incident.service in (event.involved_object.name or ""):
                evidence.append(
                    Evidence(
                        source=self.name,
                        title=f"Kubernetes event: {event.reason}",
                        detail=event.message or "",
                        relevance=0.8,
                    )
                )
        return evidence

    def scale(self, deployment: str, replicas: int) -> dict[str, object]:
        if not 1 <= replicas <= 100:
            raise ValueError("Replicas must be between 1 and 100")
        body = {"spec": {"replicas": replicas}}
        result = self.apps.patch_namespaced_deployment_scale(deployment, self.namespace, body)
        return {"deployment": deployment, "replicas": result.spec.replicas}

    def restart(self, deployment: str) -> dict[str, str]:
        restarted_at = datetime.now(UTC).isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {"annotations": {"changeguard.io/restartedAt": restarted_at}}
                }
            }
        }
        self.apps.patch_namespaced_deployment(deployment, self.namespace, body)
        return {"deployment": deployment, "restarted_at": restarted_at}
