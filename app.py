from pathlib import Path

import streamlit as st

from changeguard.adapters import DemoEvidenceProvider
from changeguard.adapters.argocd import ArgoCDAdapter
from changeguard.adapters.kubernetes import KubernetesAdapter
from changeguard.adapters.prometheus import PrometheusProvider
from changeguard.config import get_settings
from changeguard.demo import telemetry_incident
from changeguard.domain.models import IncidentStatus
from changeguard.domain.risk import ChangeRiskEngine
from changeguard.intelligence.investigator import Investigator
from changeguard.intelligence.knowledge import KnowledgeBase
from changeguard.services.approval import ApprovalService
from changeguard.services.audit import AuditLog
from changeguard.services.remediation import RemediationService

st.set_page_config(page_title="ChangeGuard", page_icon="CG", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;600;700&display=swap');
    :root { --ink:#15221b; --paper:#f4f6f1; --signal:#e45532; --safe:#187b57; --line:#cfd7ce; }
    .stApp { background: var(--paper); color: var(--ink); font-family: 'Manrope', sans-serif; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif; letter-spacing: 0; }
    code, [data-testid="stMetricValue"] { font-family: 'DM Mono', monospace; }
    [data-testid="stSidebar"] { background: #e8ede6; border-right: 1px solid var(--line); }
    [data-testid="stMetric"] { border-top: 3px solid var(--ink); padding-top: 12px; }
    .incident-band { border-left: 5px solid var(--signal); padding: 8px 16px; margin: 8px 0 22px; }
    .eyebrow {
        font-family:'DM Mono',monospace; font-size:12px;
        text-transform:uppercase; color:#536159;
    }
    .status-high { color: var(--signal); font-weight: 700; }
    .evidence { border-bottom: 1px solid var(--line); padding: 12px 0; }
    .stButton > button { border-radius: 4px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

settings = get_settings()


@st.cache_resource
def safety_services(audit_path: str, ttl_seconds: int) -> tuple[AuditLog, ApprovalService]:
    service_audit = AuditLog(Path(audit_path))
    return service_audit, ApprovalService(service_audit, ttl_seconds)


if "incident" not in st.session_state:
    st.session_state.incident = telemetry_incident()
if "report" not in st.session_state:
    st.session_state.report = None
if "approval_token" not in st.session_state:
    st.session_state.approval_token = None

incident = st.session_state.incident
audit, approvals = safety_services(str(settings.audit_path), settings.approval_ttl_seconds)
remediation = RemediationService(approvals, audit, dry_run=True)

with st.sidebar:
    st.markdown("## CHANGEGUARD")
    st.caption("Production Change Intelligence")
    mode = st.segmented_control("Evidence source", ["Demo", "Live"], default="Demo")
    api_key = st.text_input(
        "OpenAI API key",
        type="password",
        help="Held only in this Streamlit session. Leave blank for deterministic analysis.",
    )
    actor = st.text_input("On-call identity", value="on-call@changeguard.local")
    st.divider()
    st.markdown("**Environment**")
    st.code("production / us-east-1")
    st.markdown("**Safety mode**")
    st.success("Approval required · Dry run")
    if mode == "Live":
        st.warning("Configure cluster credentials and restart the app to enable live adapters.")

st.markdown(
    '<div class="eyebrow">INCIDENT COMMAND CENTER · INC-2026-0918</div>',
    unsafe_allow_html=True,
)
st.title("Vehicle telemetry processing delay")
st.markdown(
    '<div class="incident-band"><span class="status-high">HIGH SEVERITY</span> · '
    "telemetry-processing · detected 12 minutes ago · investigating</div>",
    unsafe_allow_html=True,
)

metric_columns = st.columns(4)
metric_columns[0].metric("p95 latency", "3.20 s", "+1500%")
metric_columns[1].metric("Kafka lag", "48,200", "+48,080")
metric_columns[2].metric("CPU limit", "96%", "+54 pp")
metric_columns[3].metric("Error rate", "8.4%", "+8.1 pp")

overview_tab, change_tab, investigation_tab, remediation_tab, knowledge_tab = st.tabs(
    ["Overview", "Change risk", "Investigation", "Remediation", "Knowledge"]
)

with overview_tab:
    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("Signal correlation")
        st.line_chart(
            {
                "Latency (normalized)": [1.0, 1.1, 1.0, 1.2, 4.8, 9.4, 16.0],
                "Kafka lag (normalized)": [1.0, 1.0, 1.1, 1.2, 3.2, 8.9, 15.2],
                "CPU (normalized)": [1.0, 1.2, 1.1, 1.3, 2.9, 4.8, 5.4],
            },
            height=330,
        )
    with right:
        st.subheader("Release timeline")
        st.markdown(
            """
            **22:04** · PR #418 merged  
            **22:09** · CI and security gates passed  
            **22:14** · Argo CD synced `v5.2.1`  
            **22:20** · Latency SLO burn alert fired  
            **22:22** · ChangeGuard opened investigation
            """
        )
        st.subheader("Potential blast radius")
        st.write("Vehicle ingestion → Kafka → Analytics → Safety alerts")

with change_tab:
    risk = ChangeRiskEngine().analyze(incident.change)
    score_column, detail_column = st.columns([0.35, 1])
    score_column.metric("Change risk", f"{risk.score}/100", risk.severity.value.upper())
    with detail_column:
        st.subheader("Why this change is risky")
        for factor in risk.factors:
            factor_name = factor.name.replace("_", " ").title()
            st.markdown(f"**+{factor.score} · {factor_name}**  \n{factor.reason}")
    st.subheader("Changed files")
    st.dataframe(
        [
            {"path": item.path, "additions": item.additions, "deletions": item.deletions}
            for item in incident.change.files
        ],
        width="stretch",
        hide_index=True,
    )

with investigation_tab:
    st.write("Correlate deployment, Kubernetes, Kafka, metrics, traces, and incident history.")
    if st.button("Run AI investigation", type="primary", width="stretch"):
        with st.spinner("Collecting and correlating evidence..."):
            providers = [DemoEvidenceProvider()]
            if mode == "Live":
                providers = [PrometheusProvider(settings.prometheus_url)]
                try:
                    providers.append(
                        KubernetesAdapter(
                            settings.kubernetes_namespace, settings.kubernetes_context
                        )
                    )
                except Exception:
                    st.warning("Kubernetes credentials are unavailable; continuing without them.")
                if settings.argocd_token:
                    providers.append(
                        ArgoCDAdapter(
                            settings.argocd_url,
                            settings.argocd_token.get_secret_value(),
                            settings.argocd_verify_tls,
                        )
                    )
            knowledge = None
            if api_key:
                knowledge = KnowledgeBase(
                    Path(settings.chroma_path), api_key, settings.embedding_model
                )
                knowledge.ingest(Path(settings.knowledge_path))
            investigator = Investigator(
                providers,
                api_key=api_key or None,
                model=settings.llm_model,
                knowledge_base=knowledge,
            )
            st.session_state.report = investigator.investigate(incident)
            incident.status = IncidentStatus.AWAITING_APPROVAL
    report = st.session_state.report
    if report:
        confidence_column, version_column = st.columns(2)
        confidence_column.metric("RCA confidence", f"{report.confidence:.0%}")
        version_column.metric("Responsible version", report.responsible_change or "Unknown")
        st.subheader("Root cause")
        st.write(report.root_cause)
        st.subheader("Evidence")
        for item in report.evidence:
            evidence_html = (
                f'<div class="evidence"><b>{item.source.upper()} · {item.title}</b>'
                f"<br>{item.detail}</div>"
            )
            st.markdown(
                evidence_html,
                unsafe_allow_html=True,
            )

with remediation_tab:
    report = st.session_state.report
    if not report:
        st.info("Run the investigation before requesting remediation approval.")
    else:
        recommendation = report.recommendations[0]
        st.subheader(recommendation.action.value.replace("_", " ").title())
        st.write(recommendation.rationale)
        st.write(f"**Expected outcome:** {recommendation.expected_outcome}")
        acknowledgment = st.checkbox("I reviewed the evidence and rollback plan")
        if st.button("Approve remediation", disabled=not acknowledgment):
            st.session_state.approval_token = approvals.approve(
                str(incident.id),
                recommendation.action,
                recommendation.target,
                recommendation.parameters,
                actor,
            )
            st.success("Approval recorded. The token is valid once for 15 minutes.")
        if st.button("Execute approved dry run", disabled=not st.session_state.approval_token):
            result = remediation.execute(
                st.session_state.approval_token,
                str(incident.id),
                recommendation.action,
                recommendation.target,
                actor,
            )
            st.session_state.approval_token = None
            st.json(result)

with knowledge_tab:
    st.subheader("Incident knowledge base")
    st.write("Runbooks, prior RCAs, and architecture notes are indexed locally with Chroma.")
    documents = sorted(Path(settings.knowledge_path).glob("*.md"))
    document_rows = [
        {"document": item.name, "size": f"{item.stat().st_size / 1024:.1f} KB"}
        for item in documents
    ]
    st.dataframe(
        document_rows,
        width="stretch",
        hide_index=True,
    )
