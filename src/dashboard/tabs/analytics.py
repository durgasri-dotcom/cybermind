from __future__ import annotations

import httpx
import plotly.graph_objects as go
import streamlit as st

from configs.settings import settings

import os
BACKEND = os.getenv("CYBERMIND_BACKEND_URL", f"http://127.0.0.1:{settings.api_port}{settings.api_prefix}")


def fetch_analytics():
    try:
        r = httpx.get(f"{BACKEND}/analytics/requests", timeout=5)
        return r.json()
    except Exception:
        return None


def fetch_recent_requests(limit: int = 20):
    try:
        r = httpx.get(f"{BACKEND}/analytics/requests/recent",
                      params={"limit": limit}, timeout=5)
        return r.json()
    except Exception:
        return None


def status_color(code: int, T: dict) -> str:
    if code < 300:
        return T["--green"]
    if code < 400:
        return T["--yellow"]
    if code < 500:
        return T["--orange"]
    return T["--red"]


def render(T: dict):
    st.markdown(f"""
    <div style='margin-bottom: 2rem;'>
        <div style='font-family: Rajdhani, sans-serif; font-size: 2rem; font-weight: 700;
                    color: {T["--text-primary"]}; letter-spacing: 0.05em;'>
            API ANALYTICS
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em; margin-top: 0.3rem;'>
            REAL-TIME REQUEST OBSERVABILITY · LATENCY TRACKING · ENDPOINT USAGE
        </div>
    </div>
    """, unsafe_allow_html=True)

    stats = fetch_analytics()

    # ── metrics row ───────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    if stats:
        with col1:
            st.metric("TOTAL REQUESTS", f"{stats.get('total_requests', 0):,}")
        with col2:
            st.metric("AVG LATENCY", f"{stats.get('avg_latency_ms', 0):.1f}ms")
        with col3:
            by_status = stats.get("by_status_code", {})
            success = by_status.get("200", 0) + by_status.get("201", 0)
            st.metric("2xx SUCCESS", f"{success:,}")
        with col4:
            errors = by_status.get("500", 0) + by_status.get("404", 0)
            st.metric("ERRORS", f"{errors:,}")
    else:
        for col, label in zip([col1, col2, col3, col4],
                              ["TOTAL REQUESTS", "AVG LATENCY", "2xx SUCCESS", "ERRORS"]):
            with col:
                st.metric(label, "—")

    st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                unsafe_allow_html=True)

    if not stats:
        st.warning("Backend unreachable — start the FastAPI server.")
        return

    # ── charts row ────────────────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1rem;'>
            REQUESTS BY METHOD
        </div>
        """, unsafe_allow_html=True)

        by_method = stats.get("by_method", {})
        if by_method:
            METHOD_COLORS = {
                "GET": T["--cyan"],
                "POST": T["--green"],
                "PATCH": T["--yellow"],
                "DELETE": T["--red"],
            }
            fig = go.Figure(go.Bar(
                x=list(by_method.keys()),
                y=list(by_method.values()),
                marker=dict(
                    color=[METHOD_COLORS.get(m, T["--text-dim"])
                           for m in by_method.keys()]
                ),
                hovertemplate="<b>%{x}</b><br>%{y} requests<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", size=10, color=T["--text-secondary"]),
                xaxis=dict(gridcolor=T["--border"]),
                yaxis=dict(gridcolor=T["--border"]),
                margin=dict(t=10, b=10, l=10, r=10),
                height=250,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1rem;'>
            TOP ENDPOINTS
        </div>
        """, unsafe_allow_html=True)

        top = stats.get("top_endpoints", [])
        if top:
            paths = [e["path"].replace("/api/v1/", "") for e in top]
            counts = [e["count"] for e in top]

            fig = go.Figure(go.Bar(
                x=counts,
                y=paths,
                orientation="h",
                marker=dict(color=T["--cyan"]),
                hovertemplate="<b>%{y}</b><br>%{x} requests<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", size=10, color=T["--text-secondary"]),
                xaxis=dict(gridcolor=T["--border"]),
                yaxis=dict(gridcolor=T["--border"]),
                margin=dict(t=10, b=10, l=10, r=10),
                height=250,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                unsafe_allow_html=True)

    # ── slowest endpoints ─────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                text-transform: uppercase; margin-bottom: 1rem;'>
        SLOWEST ENDPOINTS
    </div>
    """, unsafe_allow_html=True)

    slowest = stats.get("slowest_endpoints", [])
    for ep in slowest:
        latency = ep.get("latency_ms", 0)
        color = T["--green"] if latency < 100 else T["--yellow"] if latency < 500 else T["--red"]
        st.markdown(f"""
        <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                    border-left: 3px solid {color}; border-radius: 6px;
                    padding: 0.6rem 1rem; margin-bottom: 0.4rem;
                    display: flex; justify-content: space-between;'>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.8rem;
                        color: {T["--text-primary"]};'>
                <span style='color: {T["--cyan"]};'>{ep.get("method")}</span>
                &nbsp;{ep.get("path")}
            </div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.8rem;
                        color: {color}; font-weight: 600;'>
                {latency:.1f}ms
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                unsafe_allow_html=True)

    # ── recent requests feed ──────────────────────────────────────────────────
    st.markdown(f"""
    <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                text-transform: uppercase; margin-bottom: 1rem;'>
        RECENT REQUEST LOG
    </div>
    """, unsafe_allow_html=True)

    recent = fetch_recent_requests(limit=20)
    if recent and recent.get("requests"):
        for req in recent["requests"]:
            code = req.get("status_code", 0)
            color = status_color(code, T)
            st.markdown(f"""
            <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                        border-radius: 4px; padding: 0.4rem 0.8rem; margin-bottom: 0.3rem;
                        display: flex; justify-content: space-between; align-items: center;'>
                <div style='font-family: JetBrains Mono, monospace; font-size: 0.75rem;
                            color: {T["--text-secondary"]};'>
                    <span style='color: {T["--cyan"]}; margin-right: 0.5rem;'>
                        {req.get("method")}
                    </span>
                    {req.get("path")}
                </div>
                <div style='display: flex; gap: 1rem; font-family: JetBrains Mono, monospace;
                            font-size: 0.75rem;'>
                    <span style='color: {color};'>{code}</span>
                    <span style='color: {T["--text-dim"]};'>
                        {req.get("latency_ms", 0):.1f}ms
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No request logs yet — make some API calls first.")