# Telemetry Consumer Lag Runbook

## Trigger

Investigate when consumer lag exceeds 10,000 messages for five minutes or p95 processing latency
exceeds one second. Confirm the producer rate, partition count, consumer replicas, CPU throttling,
memory pressure, rebalance frequency, and `max.poll.records` before taking action.

## Mitigation

Prefer rollback when symptoms begin immediately after a deployment. Scaling consumers is safe only
up to the Kafka partition count. Record the current Argo CD revision, request human approval, roll
back one revision, and verify lag slope, p95 latency, error rate, and processed-message rate for ten
minutes. Re-sync the newer revision if rollback worsens the service.
