# Connected Vehicle Platform Architecture

Vehicle gateways publish telemetry through vehicle-data-ingestion into Kafka. The
telemetry-processing consumer validates, enriches, and routes events to analytics and safety-alert
services. Fleet dashboards consume analytics projections. A telemetry-processing delay affects data
freshness downstream but does not stop vehicle ingestion. Kafka retention provides a recovery window.

Argo CD owns Kubernetes desired state. Production mutation is forbidden outside approved workflows.
ChangeGuard has read-only access for investigation and narrowly scoped rollback, rollout restart, and
deployment scaling permissions for remediation.