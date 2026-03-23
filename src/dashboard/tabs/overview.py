import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import httpx
from configs.settings import settings

BACKEND = f"http://localhost:{settings.api_port}{settings.api_prefix}"


def fetch_health():
    try:
        r = httpx.get(f"{BACKEND}/health", timeout=5)
        return r.json()
    except Exception:
        return None


def fetch_threats_by_severity():
    try:
        r = httpx.get(f"{BACKEND}/threats/summary/by-severity", timeout=5)
        return r.json()
    except Exception:
        return None


def render():
    st.title("🛡️ CyberMind — Threat Intelligence Overview")

    health = fetch_health()

    col1, col2, col3, col4 = st.columns(4)

    if health:
        rag = health.get("services", {}).get("rag", {})
        llm = health.get("services", {}).get("llm", {})

        col1.metric("Platform Status", "Operational" if health.get("status") == "healthy" else "Degraded")
        col2.metric("Vector Store", "Ready" if rag.get("ready") else "Not Ready")
        col3.metric("Threats Indexed", f"{rag.get('vectors', 0):,}")
        col4.metric("LLM Model", llm.get("model", "Unknown").split("-")[0].upper())
    else:
        col1.metric("Platform Status", "Offline")
        col2.metric("Vector Store", "Unknown")
        col3.metric("Threats Indexed", "—")
        col4.metric("LLM Model", "—")
        st.warning("Backend not reachable. Start the FastAPI server first.")
        return

    st.divider()

    severity_data = fetch_threats_by_severity()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Threats by Severity")
        if severity_data:
            by_sev = severity_data.get("by_severity", {})
            labels = list(by_sev.keys())
            values = list(by_sev.values())
            colors = {
                "critical": "#ff4b4b",
                "high": "#ff8c00",
                "medium": "#ffd700",
                "low": "#00c853",
                "unknown": "#9e9e9e",
            }
            fig = go.Figure(go.Pie(
                labels=labels,
                values=values,
                marker_colors=[colors.get(l, "#9e9e9e") for l in labels],
                hole=0.4,
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                showlegend=True,
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No threat data available yet. Run the ingestion pipeline first.")

    with col_right:
        st.subheader("Platform Services")
        if health:
            services = health.get("services", {})
            rows = []
            for svc_name, svc_data in services.items():
                if isinstance(svc_data, dict):
                    status = "✅ Ready" if svc_data.get("ready", True) else "⚠️ Not Ready"
                    detail = " | ".join(f"{k}: {v}" for k, v in svc_data.items() if k != "ready")
                else:
                    status = "✅"
                    detail = str(svc_data)
                rows.append({"Service": svc_name.upper(), "Status": status, "Details": detail})

            st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Quick Stats")

    m1, m2, m3 = st.columns(3)
    m1.metric("Data Sources", "MITRE ATT&CK + NVD CVE")
    m2.metric("Embedding Model", "all-MiniLM-L6-v2")
    m3.metric("Vector Backend", "FAISS" if not settings.use_pinecone else "Pinecone")