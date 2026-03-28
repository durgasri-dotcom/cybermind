import httpx
import plotly.graph_objects as go
import streamlit as st

from configs.settings import settings

import os
BACKEND = os.getenv("CYBERMIND_BACKEND_URL", f"http://127.0.0.1:{settings.api_port}{settings.api_prefix}")


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


def status_card(label: str, value: str, color: str, T: dict):
    return f"""
    <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                border-top: 3px solid {color}; border-radius: 8px;
                padding: 1.2rem 1.4rem;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em;
                    text-transform: uppercase; margin-bottom: 0.5rem;'>{label}</div>
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.8rem;
                    font-weight: 700; color: {color};'>{value}</div>
    </div>
    """


def render(T: dict):
    st.markdown(f"""
    <div style='margin-bottom: 2rem;'>
        <div style='font-family: Rajdhani, sans-serif; font-size: 2rem; font-weight: 700;
                    color: {T["--text-primary"]}; letter-spacing: 0.05em;'>
            THREAT INTELLIGENCE OVERVIEW
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em; margin-top: 0.3rem;'>
            REAL-TIME PLATFORM STATUS · MITRE ATT&CK · NVD CVE
        </div>
    </div>
    """, unsafe_allow_html=True)

    health = fetch_health()
    col1, col2, col3, col4 = st.columns(4)

    if health:
        rag = health.get("services", {}).get("rag", {})
        llm = health.get("services", {}).get("llm", {})
        is_healthy = health.get("status") == "healthy"

        with col1:
            st.markdown(status_card(
                "PLATFORM STATUS",
                "OPERATIONAL" if is_healthy else "DEGRADED",
                T["--green"] if is_healthy else T["--red"], T
            ), unsafe_allow_html=True)
        with col2:
            st.markdown(status_card(
                "VECTOR STORE",
                "READY" if rag.get("ready") else "OFFLINE",
                T["--green"] if rag.get("ready") else T["--red"], T
            ), unsafe_allow_html=True)
        with col3:
            st.markdown(status_card(
                "THREATS INDEXED",
                f"{rag.get('vectors', 0):,}",
                T["--cyan"], T
            ), unsafe_allow_html=True)
        with col4:
            model = llm.get("model", "unknown").split("-")[0].upper()
            st.markdown(status_card("LLM ENGINE", model, T["--cyan"], T),
                        unsafe_allow_html=True)
    else:
        for col, (label, val) in zip(
            [col1, col2, col3, col4],
            [("PLATFORM STATUS", "OFFLINE"), ("VECTOR STORE", "UNKNOWN"),
             ("THREATS INDEXED", "—"), ("LLM ENGINE", "—")]
        ):
            with col:
                st.markdown(status_card(label, val, T["--text-dim"], T),
                            unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background: {T["--error-bg"]}; border: 1px solid {T["--error-border"]};
                    border-left: 3px solid {T["--red"]}; border-radius: 6px;
                    padding: 0.8rem 1rem; margin-top: 1rem;
                    font-family: JetBrains Mono, monospace; font-size: 0.8rem;
                    color: {T["--red"]};'>
            ⚠ BACKEND UNREACHABLE — Start the FastAPI server to connect
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"<div style='margin: 2rem 0; border-top: 1px solid {T['--border']};'></div>",
                unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1rem;'>
            THREAT DISTRIBUTION BY SEVERITY
        </div>
        """, unsafe_allow_html=True)

        severity_data = fetch_threats_by_severity()
        if severity_data:
            by_sev = severity_data.get("by_severity", {})
            filtered = {k: v for k, v in by_sev.items() if v > 0}

            SEV_COLORS = {
                "critical": T["--red"],
                "high": T["--orange"],
                "medium": T["--yellow"],
                "low": T["--green"],
                "unknown": T["--text-dim"],
            }

            if filtered:
                labels = list(filtered.keys())
                values = list(filtered.values())
                colors = [SEV_COLORS.get(sev, T["--text-dim"]) for sev in labels]

                fig = go.Figure(go.Pie(
                    labels=[sev.upper() for sev in labels],
                    values=values,
                    marker=dict(
                        colors=colors,
                        line=dict(color=T["--bg-primary"], width=2),
                    ),
                    hole=0.6,
                    textfont=dict(
                        family="JetBrains Mono",
                        size=11,
                        color=T["--text-primary"],
                    ),
                    hovertemplate="<b>%{label}</b><br>%{value} threats<br>%{percent}<extra></extra>",
                ))

                fig.add_annotation(
                    text=f"<b>{sum(values):,}</b><br><span style='font-size:10px'>TOTAL</span>",
                    x=0.5, y=0.5,
                    font=dict(family="Rajdhani", size=22, color=T["--cyan"]),
                    showarrow=False,
                )

                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="JetBrains Mono", color=T["--text-secondary"]),
                    showlegend=True,
                    legend=dict(
                        font=dict(
                            family="JetBrains Mono",
                            size=10,
                            color=T["--text-secondary"],
                        ),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=300,
                )
                st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1rem;'>
            PLATFORM SERVICES
        </div>
        """, unsafe_allow_html=True)

        if health:
            for svc_name, svc_data in health.get("services", {}).items():
                if isinstance(svc_data, dict):
                    ready = svc_data.get("ready", True)
                    dot_color = T["--green"] if ready else T["--red"]
                    detail = " · ".join(
                        f"{k}: {v}" for k, v in svc_data.items() if k != "ready"
                    )
                else:
                    dot_color = T["--cyan"]
                    detail = str(svc_data)

                st.markdown(f"""
                <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                            border-radius: 6px; padding: 0.7rem 1rem; margin-bottom: 0.5rem;
                            display: flex; justify-content: space-between; align-items: center;'>
                    <div style='display: flex; align-items: center; gap: 0.6rem;'>
                        <span style='color: {dot_color}; font-size: 0.7rem;'>●</span>
                        <span style='font-family: Rajdhani, sans-serif; font-weight: 600;
                                     color: {T["--text-primary"]}; letter-spacing: 0.05em;
                                     text-transform: uppercase; font-size: 0.85rem;'>
                            {svc_name}
                        </span>
                    </div>
                    <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                color: {T["--text-dim"]}; max-width: 55%; text-align: right;'>
                        {detail}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown(f"<div style='margin: 2rem 0; border-top: 1px solid {T['--border']};'></div>",
                unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                text-transform: uppercase; margin-bottom: 1rem;'>
        INTELLIGENCE STACK
    </div>
    """, unsafe_allow_html=True)

    items = [
        ("DATA SOURCES", "MITRE ATT&CK + NVD CVE"),
        ("EMBEDDING MODEL", "all-MiniLM-L6-v2"),
        ("VECTOR BACKEND", "FAISS" if not settings.use_pinecone else "Pinecone"),
        ("RAG CHUNKS", "2,374"),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                        border-radius: 8px; padding: 1rem 1.2rem;'>
                <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                            color: {T["--text-dim"]}; letter-spacing: 0.15em;
                            text-transform: uppercase; margin-bottom: 0.4rem;'>{label}</div>
                <div style='font-family: Rajdhani, sans-serif; font-size: 1rem;
                            font-weight: 600; color: {T["--text-secondary"]};'>{value}</div>
            </div>
            """, unsafe_allow_html=True)