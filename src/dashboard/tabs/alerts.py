import streamlit as st
import httpx
from configs.settings import settings

BACKEND = f"http://localhost:{settings.api_port}{settings.api_prefix}"


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
        r = httpx.patch(f"{BACKEND}/alerts/{alert_id}/status", params={"status": status}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


PRIORITY_COLORS = {"P1": "🔴", "P2": "🟠", "P3": "🟡", "P4": "🟢"}
STATUS_COLORS = {"open": "🔓", "in_progress": "🔄", "resolved": "✅", "false_positive": "❌"}


def render():
    st.title("🚨 Security Alerts")

    tab_list, tab_create = st.tabs(["Alert Feed", "Create Alert"])

    with tab_list:
        col1, col2 = st.columns([2, 1])
        with col1:
            status_filter = st.selectbox("Filter by status", ["All", "open", "in_progress", "resolved", "false_positive"])
        with col2:
            if st.button("Refresh", use_container_width=True):
                st.rerun()

        data = fetch_alerts(status=None if status_filter == "All" else status_filter)

        if "error" in data:
            st.error(f"Backend error: {data['error']}")
            return

        alerts = data.get("alerts", [])
        st.caption(f"{len(alerts)} alert(s) found")

        if not alerts:
            st.info("No alerts found.")
            return

        for alert in reversed(alerts):
            priority = alert.get("priority", "P3")
            status = alert.get("status", "open")
            icon = PRIORITY_COLORS.get(priority, "⚪")
            status_icon = STATUS_COLORS.get(status, "❓")

            with st.expander(f"{icon} [{priority}] {alert['title']} — {status_icon} {status}"):
                st.markdown(f"**Threat ID:** `{alert.get('threat_id')}`")
                st.markdown(f"**Description:** {alert.get('description')}")

                if alert.get("indicators"):
                    st.markdown("**Indicators:**")
                    for ioc in alert["indicators"]:
                        st.code(ioc)

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    if st.button("AI Triage", key=f"triage_{alert['id']}"):
                        with st.spinner("Analyzing..."):
                            result = triage_alert(alert["id"])
                        if "error" not in result:
                            st.markdown(f"**Recommendation:** {result.get('priority_recommendation')}")
                            st.markdown(result.get("reasoning", ""))
                        else:
                            st.error(result["error"])

                with col_b:
                    new_status = st.selectbox(
                        "Update status",
                        ["open", "in_progress", "resolved", "false_positive"],
                        key=f"status_{alert['id']}",
                    )

                with col_c:
                    if st.button("Update", key=f"update_{alert['id']}"):
                        update_status(alert["id"], new_status)
                        st.success("Status updated")
                        st.rerun()

    with tab_create:
        st.subheader("Create New Alert")

        with st.form("create_alert_form"):
            threat_id = st.text_input("Threat ID", placeholder="T1059.001")
            title = st.text_input("Title", placeholder="Suspicious PowerShell execution detected")
            description = st.text_area("Description", height=100)
            priority = st.selectbox("Priority", ["P1", "P2", "P3", "P4"])
            source_ip = st.text_input("Source IP (optional)")
            target_asset = st.text_input("Target Asset (optional)")
            indicators = st.text_area("Indicators (one per line)", height=80)
            submitted = st.form_submit_button("Create Alert")

        if submitted:
            if not all([threat_id, title, description]):
                st.warning("Threat ID, title, and description are required.")
            else:
                payload = {
                    "threat_id": threat_id,
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "source_ip": source_ip or None,
                    "target_asset": target_asset or None,
                    "indicators": [i.strip() for i in indicators.splitlines() if i.strip()],
                }
                result = create_alert(payload)
                if "error" not in result:
                    st.success(f"Alert #{result.get('id')} created successfully.")
                else:
                    st.error(result["error"])