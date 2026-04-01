from __future__ import annotations

import httpx
import plotly.graph_objects as go
import streamlit as st


import os
BACKEND = os.getenv("CYBERMIND_BACKEND_URL", "https://cybermind-0y0t.onrender.com/api/v1")
API_KEY = st.secrets.get("CYBERMIND_API_KEY", "cybermind-dev-key-change-in-prod")


def fetch_cve_stats():
    try:
        r = httpx.get(f"{BACKEND}/cves/stats", timeout=5)
        return r.json()
    except Exception:
        return None


def fetch_cves(severity: str | None = None, limit: int = 50):
    try:
        params = {"limit": limit}
        if severity:
            params["severity"] = severity
        r = httpx.get(f"{BACKEND}/cves", params=params, timeout=5)
        return r.json()
    except Exception:
        return None


def fetch_ingest(days: int = 7, max_results: int = 20):
    try:
        r = httpx.post(
            f"{BACKEND}/cves/ingest/recent",
            params={"days": days, "max_results": max_results},
            headers={"X-API-Key": API_KEY},
            timeout=60,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def severity_color(severity: str | None, T: dict) -> str:
    mapping = {
        "CRITICAL": T["--red"],
        "HIGH": T["--orange"],
        "MEDIUM": T["--yellow"],
        "LOW": T["--green"],
    }
    return mapping.get((severity or "").upper(), T["--text-dim"])


def render(T: dict):
    st.markdown(f"""
    <div style='margin-bottom: 2rem;'>
        <div style='font-family: Rajdhani, sans-serif; font-size: 2rem; font-weight: 700;
                    color: {T["--text-primary"]}; letter-spacing: 0.05em;'>
            CVE INTELLIGENCE
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em; margin-top: 0.3rem;'>
            LIVE NVD FEED · CVSS SCORING · MITRE ATT&CK MAPPING
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── stats row ─────────────────────────────────────────────────────────────
    stats = fetch_cve_stats()
    col1, col2, col3, col4 = st.columns(4)

    if stats:
        by_sev = stats.get("by_severity", {})
        with col1:
            st.metric("TOTAL CVEs", f"{stats.get('total', 0):,}")
        with col2:
            st.metric("CRITICAL", f"{stats.get('critical', 0):,}")
        with col3:
            st.metric("AVG CVSS", f"{stats.get('avg_cvss_score', 0.0):.2f}")
        with col4:
            high = by_sev.get("HIGH", 0)
            st.metric("HIGH", f"{high:,}")
    else:
        for col, label in zip([col1, col2, col3, col4],
                              ["TOTAL CVEs", "CRITICAL", "AVG CVSS", "HIGH"]):
            with col:
                st.metric(label, "—")

    st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                unsafe_allow_html=True)

    # ── charts row ────────────────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1rem;'>
            SEVERITY DISTRIBUTION
        </div>
        """, unsafe_allow_html=True)

        if stats:
            by_sev = {k: v for k, v in stats.get("by_severity", {}).items() if v > 0}
            if by_sev:
                SEV_COLORS = {
                    "CRITICAL": T["--red"],
                    "HIGH": T["--orange"],
                    "MEDIUM": T["--yellow"],
                    "LOW": T["--green"],
                }
                labels = list(by_sev.keys())
                values = list(by_sev.values())
                colors = [SEV_COLORS.get(s, T["--text-dim"]) for s in labels]

                fig = go.Figure(go.Pie(
                    labels=labels,
                    values=values,
                    marker=dict(colors=colors, line=dict(color=T["--bg-primary"], width=2)),
                    hole=0.6,
                    textfont=dict(family="JetBrains Mono", size=11, color=T["--text-primary"]),
                    hovertemplate="<b>%{label}</b><br>%{value} CVEs<br>%{percent}<extra></extra>",
                ))
                fig.add_annotation(
                    text=f"<b>{sum(values)}</b><br><span style='font-size:10px'>TOTAL</span>",
                    x=0.5, y=0.5,
                    font=dict(family="Rajdhani", size=22, color=T["--cyan"]),
                    showarrow=False,
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="JetBrains Mono", color=T["--text-secondary"]),
                    showlegend=True,
                    legend=dict(font=dict(family="JetBrains Mono", size=10,
                                          color=T["--text-secondary"]),
                                bgcolor="rgba(0,0,0,0)"),
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=300,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No CVE data yet — ingest CVEs below.")

    with col_right:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1rem;'>
            TOP CVEs BY RISK SCORE
        </div>
        """, unsafe_allow_html=True)

        cve_data = fetch_cves(limit=10)
        if cve_data and cve_data.get("cves"):
            cves = cve_data["cves"][:10]
            cve_ids = [c["cve_id"] for c in cves]
            risk_scores = [c["risk_score"] for c in cves]
            bar_colors = [severity_color(c.get("cvss_severity"), T) for c in cves]

            fig = go.Figure(go.Bar(
                x=risk_scores,
                y=cve_ids,
                orientation="h",
                marker=dict(color=bar_colors),
                hovertemplate="<b>%{y}</b><br>Risk Score: %{x:.2f}<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", size=10, color=T["--text-secondary"]),
                xaxis=dict(range=[0, 1], gridcolor=T["--border"],
                           tickfont=dict(size=9)),
                yaxis=dict(gridcolor=T["--border"], tickfont=dict(size=9)),
                margin=dict(t=10, b=10, l=10, r=10),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No CVE data yet.")

    st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                unsafe_allow_html=True)

    # ── ingest controls ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                text-transform: uppercase; margin-bottom: 1rem;'>
        INGEST FROM NVD
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        days = st.slider("DAYS BACK", min_value=1, max_value=30, value=7)
    with col_b:
        max_results = st.slider("MAX RESULTS", min_value=5, max_value=50, value=20)
    with col_c:
        st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
        if st.button("⬇ INGEST RECENT CVEs", use_container_width=True):
            with st.spinner("Fetching from NVD API..."):
                result = fetch_ingest(days=days, max_results=max_results)
            if "error" in result:
                st.error(f"Ingest failed: {result['error']}")
            else:
                st.success(
                    f"✓ Ingested: {result.get('ingested', 0)} new · "
                    f"Updated: {result.get('updated', 0)} · "
                    f"Total: {result.get('total', 0)}"
                )
                st.rerun()

    st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                unsafe_allow_html=True)

    # ── CVE table ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                text-transform: uppercase; margin-bottom: 1rem;'>
        CVE FEED
    </div>
    """, unsafe_allow_html=True)

    sev_filter = st.selectbox("FILTER BY SEVERITY",
                               ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
                               key="cve_sev_filter")
    cve_data = fetch_cves(
        severity=None if sev_filter == "ALL" else sev_filter,
        limit=50,
    )

    if cve_data and cve_data.get("cves"):
        for cve in cve_data["cves"]:
            sev = cve.get("cvss_severity", "UNKNOWN")
            color = severity_color(sev, T)
            techniques = ", ".join(cve.get("mitre_techniques", [])) or "—"
            cwes = ", ".join(cve.get("cwe_ids", [])) or "—"

            with st.expander(
                f"{cve['cve_id']} · CVSS {cve.get('cvss_score', '—')} · {sev}"
            ):
                st.markdown(f"""
                <div style='font-family: JetBrains Mono, monospace; font-size: 0.8rem;
                            color: {T["--text-secondary"]}; line-height: 1.6;'>
                    <div style='color: {color}; font-weight: 600; margin-bottom: 0.5rem;'>
                        {sev} · Risk Score: {cve.get('risk_score', 0):.2f}
                    </div>
                    <div style='margin-bottom: 0.5rem;'>{cve.get('description', '')}</div>
                    <div><span style='color: {T["--text-dim"]};'>CWE:</span> {cwes}</div>
                    <div><span style='color: {T["--text-dim"]};'>MITRE Techniques:</span>
                         <span style='color: {T["--cyan"]};'>{techniques}</span></div>
                    <div><span style='color: {T["--text-dim"]};'>Published:</span>
                         {cve.get('published_date', '—')}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No CVEs found. Use the ingest controls above to fetch from NVD.")
