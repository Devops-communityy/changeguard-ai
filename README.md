🚗 ChangeGuard
### AI-Powered Production Change Intelligence for Connected & Autonomous Vehicle Platforms  Project 2

*Production-grade DevOps + GitOps + Kubernetes + Observability + RAG + MCP + AI*

---

## Who We Are

Quantum Vector is part of TheDevOpsCommunity  a DevOps and AI education platform built by people who work in DevOps, SRE, and AI engineering roles, not just people who teach them.

A few quick facts about us:

- We've grown a DevOps community of **165,000+ engineers** over the last 1.5+ years, across Instagram, WhatsApp, Threads, and LinkedIn.
- We've run **20+ live cohorts** and delivered **10+ full production-style projects**.
- Our instructor team is made up of working engineers with **11 to 16+ years** of hands-on experience.
- Our founder currently works as a Senior DevOps/SRE and AI automation engineer at a large company, building and running real production systems  not just teaching from slides.

We teach the way we work. ChangeGuard is built the way a real AI-powered ops platform would be built  not a chatbot bolted onto a dashboard.

## Dates & Timings

| Day | Date | Time (IST) |
|---|---|---|
| TBD | TBD | TBD |
| TBD | TBD | TBD |

Dates for this cohort haven't been set yet  share them and I'll drop them straight into this table.

## Why This Project Is Important

Most "AI for DevOps" content stops at a chatbot that can answer questions about your logs. ChangeGuard goes further: the AI is wired into the actual production change lifecycle. It watches a change move from a pull request through CI/CD and Argo CD into Kubernetes, watches what happens to the system afterward, and  when something breaks  investigates it using real tools (MCP) and real history (RAG), before recommending a fix that a human approves.

DevOps + SRE + practical AI agents is a rare, high-demand combination right now. Most engineers know one side or the other. ChangeGuard teaches you to build the bridge  and gives you a real story to tell in interviews, not just a certificate.

## What You Will Learn

- **Git & GitOps**  pull requests, change history, Git-based desired state
- **CI/CD**  Jenkins/GitHub Actions, automated build, test and security gates
- **Docker**  packaging production services as containers
- **Kubernetes / EKS**  running and scaling microservices
- **Argo CD**  GitOps-based deployment and reconciliation
- **Kafka**  high-volume event streaming
- **Observability**  Prometheus, Grafana, centralized logs, OpenTelemetry tracing
- **RAG**  searching past incidents, runbooks and architecture docs for relevant history
- **MCP**  giving an AI agent controlled, safe access to live Git, Argo CD, Kubernetes, Kafka and observability tools
- **AI agent design**  change-risk scoring, anomaly detection, root cause analysis, blast-radius analysis, controlled remediation
- **Human-in-the-loop safety**  why sensitive production actions need human approval, and how to build that in

You'll also work through real incidents on purpose  a bad deployment that spikes latency, a Kafka consumer crash, a memory leak, a database outage, a traffic spike, and more  with the AI agent as your investigation partner, not just a search bar.

## Architecture

```
Developer → Git/GitHub → AI Change Analysis → CI/CD → Docker → Container Registry
→ Argo CD → Kubernetes/EKS → Services → Kafka → Observability
(Prometheus, Grafana, Logs, OpenTelemetry) → MCP Tool Layer → AI Agent
(RAG + Risk Engine + RCA + Blast Radius) → Human Approval → Controlled Remediation
```

**The MCP Tool Layer connects the AI agent to:**
```
Git MCP · Argo CD MCP · Kubernetes MCP · Kafka MCP · Observability MCP
```

## Tools We Use

| Area | Tools |
|---|---|
| Source Control & GitOps | Git, GitHub/GitLab, Argo CD |
| CI/CD | Jenkins, GitHub Actions |
| Containers & Cloud | Docker, AWS, EKS, Terraform |
| Orchestration | Kubernetes, Helm |
| Streaming | Kafka |
| Observability | Prometheus, Grafana, centralized logs, OpenTelemetry |
| AI Engineering | LLM agents, RAG, embeddings/vector search, tool calling |
| MCP | Custom MCP servers for safe infrastructure access |
| SRE | Incident response, RCA, SLOs, change risk |
| Security | Secrets, IAM/RBAC, approval controls |

## Prerequisites

This is a **production project**, not a beginner tutorial. Before joining, you should already know:

- Basic DevOps (Git, Docker, Kubernetes basics)
- A basic idea of CI/CD and cloud/AWS
- A basic idea of what an LLM/AI agent is (helpful, not mandatory)

**Important  please read this before joining:**
Don't expect us to teach every tool from zero. We won't spend time explaining "what is Docker" or "what is Kubernetes" from scratch  and we won't spend time on "what is an LLM" either. This project moves at a production pace and focuses on how DevOps and AI work together in one real system. If you're new to DevOps, start with a beginner-friendly course first.

---

*ChangeGuard  Project 2 of the Quantum Vector Production DevOps Project series.*
