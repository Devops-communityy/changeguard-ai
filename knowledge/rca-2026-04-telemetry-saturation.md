# RCA: Telemetry Consumer Saturation

Version 4.8.3 increased `max.poll.records` while reducing pod CPU from 500m to 250m. Consumers spent
too long processing each poll, exceeded expected cycle time, and accumulated lag. Vehicle analytics
and safety alert freshness degraded, but ingestion remained available.

The team rolled back with Argo CD after approval. Lag returned below 500 in eight minutes. Preventive
actions were a CPU-throttling alert, a load-test gate for consumer configuration, and a policy that
consumer resource reductions require performance evidence.
