import httpx
import streamlit as st

from configs.settings import settings

BACKEND = f"http://127.0.0.1:{settings.api_port}{settings.api_prefix}"


def fetch_alerts(status=None):
    try:
        params = {"limit": 100}
        if status:
            params["status"] = status
        r = httpx.get(f"{BACKEND}/alerts", params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def create_alert(payload: dict):
    try:
        r = httpx.post(f"{BACKEND}/alerts", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def triage_alert(alert_id: int):
    try:
        r = httpx.post(f"{BACKEND}/alerts/{alert_id}/triage", timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def update_status(alert_id: int, status: str):
    try:
        r = httpx.patch(f"{BACKEND}/alerts/{alert_id}/status",
                        params={"status": status}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def render(T: dict):
    st.markdown(f"""
    <div style='margin-bottom: 2rem;'>
        <div style='font-family: Rajdhani, sans-serif; font-size: 2rem; font-weight: 700;
                    color: {T["--text-primary"]}; letter-spacing: 0.05em;'>
            SECURITY ALERTS
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em; margin-top: 0.3rem;'>
            ALERT TRIAGE · AI-ASSISTED ANALYSIS · SOC WORKFLOW
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_list, tab_create = st.tabs(["ALERT FEED", "CREATE ALERT"])

    with tab_list:
        col1, col2 = st.columns([3, 1])
        with col1:
            status_filter = st.selectbox(
                "FILTER BY STATUS",
                ["All", "open", "in_progress", "resolved", "false_positive"],
                key="alert_filter",
            )
        with col2:
            st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
            if st.button("↻ REFRESH", use_container_width=True):
                st.rerun()

        data = fetch_alerts(status=None if status_filter == "All" else status_filter)

        if "error" in data:
            st.markdown(f"""
            <div style='background: {T["--error-bg"]}; border: 1px solid {T["--error-border"]};
                        border-left: 3px solid {T["--red"]}; border-radius: 6px;
                        padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                        font-size: 0.8rem; color: {T["--red"]};'>⚠ {data["error"]}</div>
            """, unsafe_allow_html=True)
            return

        alerts = data.get("alerts", [])
        st.markdown(f"""
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.1em; margin-bottom: 1rem;'>
            {len(alerts)} ALERT(S) FOUND
        </div>
        """, unsafe_allow_html=True)

        P_COLORS = {
            "P1": T["--red"], "P2": T["--orange"],
            "P3": T["--yellow"], "P4": T["--green"],
        }
        P_LABELS = {"P1": "CRITICAL", "P2": "HIGH", "P3": "MEDIUM", "P4": "LOW"}
        S_ICONS = {
            "open": "●", "in_progress": "◑",
            "resolved": "✓", "false_positive": "✕",
        }

        if not alerts:
            st.markdown(f"""
            <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                        border-radius: 8px; padding: 2rem; text-align: center;
                        font-family: JetBrains Mono, monospace; font-size: 0.8rem;
                        color: {T["--text-dim"]};'>NO ALERTS FOUND</div>
            """, unsafe_allow_html=True)
        else:
            for alert in reversed(alerts):
                priority = alert.get("priority", "P3")
                status = alert.get("status", "open")
                p_color = P_COLORS.get(priority, T["--text-dim"])
                p_label = P_LABELS.get(priority, priority)
                s_icon = S_ICONS.get(status, "?")

                with st.expander(f"[{p_label}]  {alert['title']}"):
                    st.markdown(f"""
                    <div style='display: flex; gap: 0.6rem; margin-bottom: 1rem;
                                flex-wrap: wrap; align-items: center;'>
                        <span style='background: {p_color}22; border: 1px solid {p_color}55;
                                     border-radius: 4px; padding: 0.2rem 0.6rem;
                                     font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                     color: {p_color}; letter-spacing: 0.08em;'>
                            {priority} · {p_label}
                        </span>
                        <span style='background: {T["--tag-bg"]}; border: 1px solid {T["--border"]};
                                     border-radius: 4px; padding: 0.2rem 0.6rem;
                                     font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                     color: {T["--text-secondary"]}; letter-spacing: 0.08em;'>
                            {s_icon} {status.upper()}
                        </span>
                        <span style='background: {T["--cyan-dim"]}; border: 1px solid {T["--cyan"]}44;
                                     border-radius: 4px; padding: 0.2rem 0.6rem;
                                     font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                     color: {T["--cyan"]}; letter-spacing: 0.08em;'>
                            {alert.get("threat_id")}
                        </span>
                    </div>
                    <div style='font-family: Inter, sans-serif; font-size: 0.88rem;
                                color: {T["--text-secondary"]}; margin-bottom: 1rem;
                                line-height: 1.6;'>
                        {alert.get("description", "")}
                    </div>
                    """, unsafe_allow_html=True)

                    if alert.get("indicators"):
                        st.markdown(f"""
                        <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                    color: {T["--text-dim"]}; letter-spacing: 0.1em;
                                    margin-bottom: 0.5rem;'>INDICATORS OF COMPROMISE</div>
                        """, unsafe_allow_html=True)
                        for ioc in alert["indicators"]:
                            st.markdown(f"""
                            <div style='background: {T["--input-bg"]}; border: 1px solid {T["--border"]};
                                        border-left: 2px solid {T["--orange"]}; border-radius: 4px;
                                        padding: 0.3rem 0.7rem; margin-bottom: 0.3rem;
                                        font-family: JetBrains Mono, monospace; font-size: 0.75rem;
                                        color: {T["--orange"]};'>{ioc}</div>
                            """, unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("⟶ AI TRIAGE", key=f"triage_{alert['id']}"):
                            with st.spinner("Analyzing..."):
                                result = triage_alert(alert["id"])
                            if "error" not in result:
                                st.markdown(f"""
                                <div style='background: {T["--bg-card"]};
                                            border: 1px solid {T["--cyan"]}44;
                                            border-left: 3px solid {T["--cyan"]};
                                            border-radius: 6px; padding: 1rem;
                                            margin-top: 0.5rem; font-family: Inter, sans-serif;
                                            font-size: 0.85rem; color: {T["--text-primary"]};
                                            line-height: 1.6;'>
                                    {result.get("reasoning", "")}
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.error(result["error"])
                    with col_b:
                        new_status = st.selectbox(
                            "UPDATE STATUS",
                            ["open", "in_progress", "resolved", "false_positive"],
                            key=f"status_{alert['id']}",
                        )
                    with col_c:
                        st.markdown("<div style='margin-top: 1.8rem;'></div>",
                                    unsafe_allow_html=True)
                        if st.button("UPDATE", key=f"update_{alert['id']}"):
                            update_status(alert["id"], new_status)
                            st.rerun()

    with tab_create:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1.5rem;'>
            CREATE SECURITY ALERT
        </div>
        """, unsafe_allow_html=True)

        threat_id = st.text_input("THREAT ID", placeholder="T1059.001",
                                   key="new_threat_id")
        title = st.text_input("TITLE",
                               placeholder="Suspicious PowerShell execution detected",
                               key="new_title")
        description = st.text_area("DESCRIPTION", height=100, key="new_description")
        priority = st.selectbox("PRIORITY", ["P1", "P2", "P3", "P4"],
                                 key="new_priority")
        source_ip = st.text_input("SOURCE IP (optional)", key="new_source_ip")
        target_asset = st.text_input("TARGET ASSET (optional)", key="new_target_asset")
        indicators = st.text_area("INDICATORS — one per line", height=80,
                                   key="new_indicators")

        if st.button("⟶ CREATE ALERT", type="primary"):
            if not all([threat_id, title, description]):
                st.markdown(f"""
                <div style='background: {T["--warn-bg"]}; border: 1px solid {T["--warn-border"]};
                            border-left: 3px solid {T["--yellow"]}; border-radius: 6px;
                            padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                            font-size: 0.75rem; color: {T["--yellow"]};'>
                    ⚠ THREAT ID, TITLE, AND DESCRIPTION REQUIRED
                </div>
                """, unsafe_allow_html=True)
            else:
                payload = {
                    "threat_id": threat_id,
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "source_ip": source_ip or None,
                    "target_asset": target_asset or None,
                    "indicators": [i.strip() for i in
                                   indicators.splitlines() if i.strip()],
                }
                result = create_alert(payload)
                if "error" not in result:
                    st.markdown(f"""
                    <div style='background: {T["--success-bg"]};
                                border: 1px solid {T["--success-border"]};
                                border-left: 3px solid {T["--green"]}; border-radius: 6px;
                                padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                                font-size: 0.75rem; color: {T["--green"]};'>
                        ✓ ALERT #{result.get("id")} CREATED SUCCESSFULLY
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(result["error"])