# ChangeGuard

AI-powered production change intelligence for connected and autonomous vehicle platforms.
ChangeGuard correlates Git changes, deployments, Kubernetes state, Kafka health, metrics, logs,
traces, and incident history to produce an evidence-backed RCA. Remediation is separately approved,
scope-bound, audited, and single-use.

## Architecture

```text
Git / PR ──> Risk Engine ──> CI/CD ──> Argo CD ──> Kubernetes / Kafka
                  │                                  │
                  └──────── Change Context           ├── Prometheus
                                                     ├── Logs / OTel
                                                     └── Kubernetes events
                                                              │
Knowledge base ──> Chroma / RAG ──> LangChain Investigator <──┘
                                         │
                                         v
                       RCA + confidence + blast radius
                                         │
                                         v
                     Human approval ──> controlled action ──> verify
```

The deterministic risk engine and safety controls do not depend on an LLM. LangChain uses structured
Pydantic output, and retrieved text/tool output is explicitly treated as untrusted evidence. When no
OpenAI key is supplied, the demo runs with deterministic investigation logic.

## Repository

```text
app.py                          Streamlit incident command center
src/changeguard/api.py         FastAPI automation/control plane
src/changeguard/domain/        Typed models and explainable risk engine
src/changeguard/intelligence/  LangChain investigation and Chroma RAG
src/changeguard/adapters/      GitHub, Prometheus, Kubernetes, Argo CD
src/changeguard/services/      Approval, audit, and remediation controls
src/changeguard/mcp_server.py  MCP read-only evidence tools
knowledge/                     Runbooks, RCAs, architecture documents
deploy/helm/                   Kubernetes Helm chart
deploy/argocd/                 GitOps Application
observability/                 Prometheus alert rules
```

## Local Run

Python 3.12+ is required.

```bash
make install
make test
make run
```

Open `http://localhost:8501`. Enter an OpenAI API key in the sidebar for LangChain RCA and RAG, or
leave it blank for deterministic demo mode. The key is kept in Streamlit session memory and is not
written to disk.

Run the API separately:

```bash
make api
curl http://localhost:8080/healthz
```

Or run both services in containers:

```bash
docker compose up --build
```

## API Workflow

Analyze a change with `POST /v1/changes/risk`, investigate with
`POST /v1/incidents/investigate`, then approve and execute through separate calls:

```bash
curl -X POST http://localhost:8080/v1/remediations/approve \
  -H 'Content-Type: application/json' \
  -H 'X-Actor: on-call@example.com' \
  -d '{
    "incident_id":"incident-id",
    "action":"argo_rollback",
    "target":"telemetry-processing",
    "parameters":{"revision_id":4}
  }'
```

The returned token is hashed at rest, expires after 15 minutes, is bound to incident/action/target,
and is consumed once. Development defaults to dry-run. Production action adapters must be configured
and should be protected by an identity-aware API gateway; `X-Actor` alone is not authentication.

## Live Integrations

Configuration uses `CHANGEGUARD_` environment variables. Copy `.env.example` for non-secret values.
Secrets may be provided by Kubernetes Secrets or an external secret operator. The UI intentionally
supports direct entry of the OpenAI key.

Important settings:

| Setting | Purpose |
|---|---|
| `CHANGEGUARD_DEMO_MODE` | Dry-run remediations when `true` |
| `CHANGEGUARD_PROMETHEUS_URL` | Prometheus HTTP API |
| `CHANGEGUARD_ARGOCD_URL` | Argo CD API |
| `CHANGEGUARD_ARGOCD_TOKEN` | Narrowly scoped Argo CD token |
| `CHANGEGUARD_KUBERNETES_NAMESPACE` | Investigated workload namespace |
| `CHANGEGUARD_GITHUB_TOKEN` | Read-only GitHub token |

The Kubernetes adapter first tries in-cluster credentials and then the configured kube context. Its
RBAC permits read access to pods/events and narrowly scoped deployment patch/scale operations. Split
investigation and remediation service accounts in regulated environments.

## MCP

`.vscode/mcp.json` registers the local server. It currently exposes a safe read-only incident evidence
tool and is the extension point for additional Git, Argo CD, Kubernetes, Kafka, and observability
tools. Mutating actions belong behind `ApprovalService`; do not expose raw mutation tools to the AI.

## GitOps Deployment

```bash
helm template changeguard deploy/helm/changeguard --namespace changeguard
helm upgrade --install changeguard deploy/helm/changeguard \
  --namespace changeguard --create-namespace \
  --set image.repository=ghcr.io/YOUR_ORG/changeguard-ai \
  --set image.tag=YOUR_IMMUTABLE_SHA
kubectl apply -f deploy/argocd/application.yaml
```

Create `changeguard-secrets` before installation or remove the secret reference when only direct UI
key entry is used. In production, replace the sample repository URL and image repository, use an
external secret manager, persist audit events to a SIEM, and place UI/API behind SSO.

## Production Controls

- Non-root, read-only containers with dropped capabilities
- Readiness/liveness probes, HPA, PDB, and default-deny network policy
- Explainable pre-deployment risk scoring independent of the LLM
- Provider failure isolation and evidence provenance
- Hash-chained append-only audit records
- Expiring, scope-bound, one-time approval tokens
- Dry-run default and reversible remediation recommendations
- CI lint, typing, tests, dependency audit, container scan, and immutable SHA images

The in-process approval store is suitable for local/demo operation. A production multi-replica API
must replace it with a transactional shared store such as Redis or PostgreSQL and send audit records
to durable centralized storage. This boundary is deliberately represented by `ApprovalService` and
can be swapped without changing the investigator.

## Validation

```bash
make lint
make typecheck
make test
helm template changeguard deploy/helm/changeguard --namespace changeguard
docker compose config --quiet
```
