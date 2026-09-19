# ChangeGuard Notes

## What Is ChangeGuard?

ChangeGuard is an AI-assisted production change safety and incident-response platform.

It connects:

- GitHub pull requests
- CI/CD deployments
- Kubernetes
- Argo CD
- Prometheus metrics
- Historical runbooks and RCAs
- Human approvals
- Remediation actions
- Audit logging

Its main question is:

> Did a recent production change cause the incident, and what is the safest approved action?

## Problem It Solves

During incidents, important information is spread across many systems. Engineers must manually compare:

- Recent code changes
- Deployment versions
- Error rates
- Latency
- CPU and memory
- Kubernetes events
- Pod health
- Kafka consumer lag
- Previous incidents and runbooks

This can lead to:

- Slow root-cause analysis
- Incorrect assumptions
- Risky manual commands
- Unapproved production changes
- Repeated operational mistakes
- Incomplete audit history

ChangeGuard brings this process into one controlled workflow.

## Main Workflow

```text
Pull request or deployment
        |
        v
Change risk analysis
        |
        v
Production incident investigation
        |
        v
Evidence collection
        |
        v
Root-cause report
        |
        v
Human approval
        |
        v
Controlled remediation
        |
        v
Audit record
```

## Change Risk Analysis

ChangeGuard evaluates whether a code or infrastructure change is risky.

It considers:

- Number of changed lines
- Critical files
- Kubernetes or Helm changes
- Terraform changes
- Database migrations
- Kafka consumer changes
- Telemetry changes
- CPU and memory settings
- Replica counts
- Timeout configuration
- Cross-service impact
- Missing tests

The result is a risk level such as:

- Low
- Medium
- High
- Critical

## Incident Investigation

When an incident occurs, ChangeGuard collects operational evidence from connected systems.

Example evidence:

- Prometheus error rate
- Prometheus p95 latency
- Pod CPU and memory
- Kubernetes pod status
- Kubernetes events
- Argo CD health and sync status
- Recent deployment versions
- Historical incident reports
- Operational runbooks

The investigation report can contain:

- Probable root cause
- Responsible version
- Confidence level
- Affected services
- Evidence supporting the conclusion
- Recommended remediation
- Expected blast radius

The AI layer improves the investigation, but the application also has deterministic fallback logic. It does not need an LLM for the basic safety workflow.

## Example Production Scenario

A telemetry consumer is deployed to production.

After deployment:

- Kafka consumer lag increases
- Processing latency increases
- CPU usage becomes high
- Telemetry becomes delayed
- Downstream services receive stale data

ChangeGuard can:

1. Identify the recent deployment.
2. Compare the deployment with the incident timing.
3. Inspect Prometheus and Kubernetes evidence.
4. Check whether the change affected consumer behavior or resource limits.
5. Search similar runbooks and previous RCAs.
6. Produce an evidence-backed RCA.
7. Recommend rollback, scaling, or rollout restart.
8. Wait for SRE approval.
9. Execute only the approved action.
10. Record the complete activity in the audit log.

## Supported Remediation Actions

The current system supports:

- `argo_rollback`
- `scale_deployment`
- `restart_rollout`

Remediation can run in dry-run mode or invoke Kubernetes and Argo CD adapters.

## Approval Controls

Before remediation, an engineer must approve a specific action.

Approval tokens are:

- Cryptographically random
- Time-limited
- Single-use
- Bound to an incident
- Bound to an action
- Bound to a target
- Bound to the approved parameters

For example, approval to scale `telemetry-consumer` cannot be reused to restart another service.

## Auditability

ChangeGuard records:

- Who approved the action
- Which incident was involved
- Which action was approved
- Which target was affected
- When the action was executed
- Whether execution succeeded or failed

The audit records use hash chaining to make later tampering detectable.

## Users

### SREs and On-Call Engineers

Investigate incidents, review evidence, approve actions, and monitor remediation.

### Platform Engineers

Connect Kubernetes, Argo CD, Prometheus, GitHub, and deployment systems.

### Developers

Understand the production risk of their changes.

### Release Managers

Require additional review for high-risk changes.

### Security and Compliance Teams

Review production actions and audit history.

## What ChangeGuard Does Not Replace

ChangeGuard does not replace:

- Kubernetes
- Argo CD
- Prometheus
- GitHub
- CI/CD systems
- Incident-management platforms
- Human SRE judgment

It coordinates information from these systems and adds investigation, approval, and safety controls.

## Current Project Components

| Component | Purpose |
|---|---|
| `src/changeguard/domain/risk.py` | Calculates change risk |
| `src/changeguard/intelligence/investigator.py` | Investigates incidents |
| `src/changeguard/intelligence/knowledge.py` | Searches runbooks and RCAs |
| `src/changeguard/services/approval.py` | Creates and consumes approvals |
| `src/changeguard/services/remediation.py` | Executes approved actions |
| `src/changeguard/services/audit.py` | Writes audit records |
| `src/changeguard/adapters/github.py` | Reads GitHub change information |
| `src/changeguard/adapters/prometheus.py` | Collects Prometheus evidence |
| `src/changeguard/adapters/kubernetes.py` | Collects Kubernetes evidence and executes actions |
| `src/changeguard/adapters/argocd.py` | Reads Argo CD state and performs rollback |
| `app.py` | Streamlit incident command center |
| `src/changeguard/api.py` | FastAPI control-plane API |

## Production Readiness Gaps

Before using this system for real production remediation, it needs:

- Shared approval storage such as Redis or PostgreSQL
- Real authentication and authorization
- Durable centralized audit storage
- Stronger Kubernetes and Argo CD credential management
- Policy checks for remediation parameters
- Concurrency protection for simultaneous actions
- Post-remediation health verification
- Real CI/CD and incident-management integrations
- Production log and trace ingestion
- Full end-to-end testing against real infrastructure

## Summary

ChangeGuard is a safety and intelligence layer for production operations.

Its value is:

```text
Understand risky changes
        +
Correlate incidents with deployments
        +
Recommend evidence-backed fixes
        +
Require human approval
        +
Execute controlled remediation
        +
Maintain an audit trail
```

In simple terms:

> ChangeGuard helps engineering teams determine whether a recent change caused a production problem and safely recover without relying entirely on manual investigation and emergency commands.
