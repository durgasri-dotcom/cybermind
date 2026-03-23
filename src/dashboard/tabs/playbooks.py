import streamlit as st
import httpx
from configs.settings import settings

BACKEND = f"http://localhost:{settings.api_port}{settings.api_prefix}"


def fetch_playbooks():
    try:
        r = httpx.get(f"{BACKEND}/playbooks", params={"limit": 50}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def generate_playbook(payload: dict):
    try:
        r = httpx.post(f"{BACKEND}/playbooks/generate", json=payload, timeout=90)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


TEAM_ICONS = {
    "SOC Tier 1": "",
    "SOC Tier 2": "",
    "IR Team": "",
    "Management": "",
    "IT Operations": "",
}


def render():
    st.title("📋 Incident Response Playbooks")

    tab_list, tab_generate = st.tabs(["Saved Playbooks", "Generate Playbook"])

    with tab_list:
        if st.button("Refresh", use_container_width=False):
            st.rerun()

        data = fetch_playbooks()

        if "error" in data:
            st.error(f"Backend error: {data['error']}")
            return

        playbooks = data.get("playbooks", [])
        st.caption(f"{len(playbooks)} playbook(s) available")

        if not playbooks:
            st.info("No playbooks yet. Generate one from the Generate tab.")
            return

        for pb in reversed(playbooks):
            with st.expander(f" {pb.get('title')} — {pb.get('threat_id')}"):
                st.markdown(f"**Objective:** {pb.get('objective')}")
                st.markdown(f"**Status:** `{pb.get('status')}`")
                st.markdown(f"**Generated:** {pb.get('generated_at', '')[:19].replace('T', ' ')}")

                steps = pb.get("steps", [])
                if steps:
                    st.divider()
                    st.markdown("**Response Steps:**")
                    for step in steps:
                        team = step.get("responsible_team", "SOC Tier 1")
                        icon = TEAM_ICONS.get(team, "👤")
                        tools = step.get("tools", [])
                        tools_str = f" · Tools: {', '.join(tools)}" if tools else ""
                        time_str = f" · ~{step.get('estimated_minutes', 30)} min"

                        st.markdown(
                            f"**Step {step['step_number']}: {step['action']}**  \n"
                            f"{icon} {team}{tools_str}{time_str}"
                        )
                        if step.get("notes"):
                            st.caption(step["notes"])
                        st.divider()

                tags = pb.get("tags", [])
                if tags:
                    st.markdown(" ".join(f"`{t}`" for t in tags))

    with tab_generate:
        st.subheader("Generate AI Playbook")
        st.caption("CyberMind will generate a structured incident response playbook for any MITRE technique or CVE.")

        with st.form("generate_form"):
            threat_id = st.text_input("Threat ID", placeholder="T1486 — Data Encrypted for Impact")
            context = st.text_area(
                "Additional Context (optional)",
                placeholder="e.g. Ransomware detected on 3 Windows servers in finance department",
                height=100,
            )
            tools_input = st.text_input(
                "Available SOC Tools (comma separated)",
                placeholder="Splunk, CrowdStrike, Microsoft Sentinel",
            )
            submitted = st.form_submit_button("Generate Playbook")

        if submitted:
            if not threat_id.strip():
                st.warning("Threat ID is required.")
            else:
                tools = [t.strip() for t in tools_input.split(",") if t.strip()]
                payload = {
                    "threat_id": threat_id.strip(),
                    "context": context.strip(),
                    "include_tools": tools,
                }
                with st.spinner("Generating playbook..."):
                    result = generate_playbook(payload)

                if "error" in result:
                    st.error(f"Error: {result['error']}")
                    return

                st.success(f"Playbook #{result.get('id')} generated successfully.")
                st.divider()
                st.markdown(f"### {result.get('title')}")
                st.markdown(f"**Objective:** {result.get('objective')}")

                steps = result.get("steps", [])
                for step in steps:
                    team = step.get("responsible_team", "SOC Tier 1")
                    icon = TEAM_ICONS.get(team, "👤")
                    tools_used = step.get("tools", [])
                    tools_str = f" · Tools: {', '.join(tools_used)}" if tools_used else ""

                    st.markdown(
                        f"**Step {step['step_number']}: {step['action']}**  \n"
                        f"{icon} {team}{tools_str} · ~{step.get('estimated_minutes', 30)} min"
                    )
                    if step.get("notes"):
                        st.caption(step["notes"])
                    st.divider()