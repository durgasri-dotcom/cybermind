import httpx
import streamlit as st

from configs.settings import settings

import os
BACKEND = os.getenv("CYBERMIND_BACKEND_URL", f"http://127.0.0.1:{settings.api_port}{settings.api_prefix}")


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


TEAM_CONFIG = {
    "SOC Tier 1":    ("--cyan",   "◈"),
    "SOC Tier 2":    ("--cyan",   "◉"),
    "IR Team":       ("--orange", "⬡"),
    "Management":    ("--text-secondary", "◇"),
    "IT Operations": ("--green",  "⬢"),
}


def step_card(step: dict, T: dict) -> str:
    team = step.get("responsible_team", "SOC Tier 1")
    color_key, icon = TEAM_CONFIG.get(team, ("--text-secondary", "○"))
    color = T[color_key]
    tools = step.get("tools", [])
    tools_str = " · ".join(tools) if tools else "—"
    notes = step.get("notes", "")

    return f"""
    <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                border-left: 3px solid {color}; border-radius: 6px;
                padding: 0.9rem 1rem; margin-bottom: 0.5rem;'>
        <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
            <div style='flex: 1;'>
                <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                            color: {color}; letter-spacing: 0.1em; margin-bottom: 0.3rem;'>
                    STEP {step["step_number"]:02d}
                </div>
                <div style='font-family: Rajdhani, sans-serif; font-size: 1rem;
                            font-weight: 600; color: {T["--text-primary"]};
                            margin-bottom: 0.4rem;'>
                    {step["action"]}
                </div>
                <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                            color: {T["--text-dim"]};'>
                    TOOLS: {tools_str}
                </div>
                {f'<div style="font-family: Inter, sans-serif; font-size: 0.8rem; color: {T["--text-secondary"]}; margin-top: 0.4rem; line-height: 1.5;">{notes[:200]}</div>' if notes else ""}
            </div>
            <div style='text-align: right; flex-shrink: 0; margin-left: 1rem;'>
                <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                            color: {color};'>{icon} {team}</div>
                <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                            color: {T["--text-dim"]}; margin-top: 0.3rem;'>
                    ~{step.get("estimated_minutes", 30)} min
                </div>
            </div>
        </div>
    </div>
    """


def render(T: dict):
    st.markdown(f"""
    <div style='margin-bottom: 2rem;'>
        <div style='font-family: Rajdhani, sans-serif; font-size: 2rem; font-weight: 700;
                    color: {T["--text-primary"]}; letter-spacing: 0.05em;'>
            INCIDENT RESPONSE PLAYBOOKS
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em; margin-top: 0.3rem;'>
            AI-GENERATED · MITRE ATT&CK · STRUCTURED RESPONSE WORKFLOWS
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_list, tab_generate = st.tabs(["SAVED PLAYBOOKS", "GENERATE PLAYBOOK"])

    with tab_list:
        if st.button("↻ REFRESH", use_container_width=False):
            st.rerun()

        data = fetch_playbooks()

        if "error" in data:
            st.markdown(f"""
            <div style='background: {T["--error-bg"]}; border: 1px solid {T["--error-border"]};
                        border-left: 3px solid {T["--red"]}; border-radius: 6px;
                        padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                        font-size: 0.8rem; color: {T["--red"]};'>⚠ {data["error"]}</div>
            """, unsafe_allow_html=True)
            return

        playbooks = data.get("playbooks", [])
        st.markdown(f"""
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.1em; margin-bottom: 1rem;'>
            {len(playbooks)} PLAYBOOK(S) AVAILABLE
        </div>
        """, unsafe_allow_html=True)

        if not playbooks:
            st.markdown(f"""
            <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                        border-radius: 8px; padding: 2rem; text-align: center;
                        font-family: JetBrains Mono, monospace; font-size: 0.8rem;
                        color: {T["--text-dim"]};'>
                NO PLAYBOOKS — Generate one from the Generate tab
            </div>
            """, unsafe_allow_html=True)
        else:
            for pb in reversed(playbooks):
                with st.expander(f"⬡  {pb.get('title')} — {pb.get('threat_id')}"):
                    st.markdown(f"""
                    <div style='display: flex; gap: 0.6rem; margin-bottom: 1rem; flex-wrap: wrap;'>
                        <span style='background: {T["--cyan-dim"]}; border: 1px solid {T["--cyan"]}44;
                                     border-radius: 4px; padding: 0.2rem 0.6rem;
                                     font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                     color: {T["--cyan"]};'>{pb.get("threat_id")}</span>
                        <span style='background: {T["--success-bg"]}; border: 1px solid {T["--success-border"]};
                                     border-radius: 4px; padding: 0.2rem 0.6rem;
                                     font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                     color: {T["--green"]};'>{pb.get("status", "").upper()}</span>
                        <span style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                     color: {T["--text-dim"]};'>
                            {pb.get("generated_at", "")[:19].replace("T", " ")} UTC
                        </span>
                    </div>
                    <div style='font-family: Inter, sans-serif; font-size: 0.88rem;
                                color: {T["--text-secondary"]}; margin-bottom: 1.2rem;
                                line-height: 1.6;'>
                        {pb.get("objective", "")}
                    </div>
                    """, unsafe_allow_html=True)

                    for step in pb.get("steps", []):
                        st.markdown(step_card(step, T), unsafe_allow_html=True)

                    tags = pb.get("tags", [])
                    if tags:
                        tags_html = " ".join([
                            f"<span style='background: {T['--tag-bg']}; border-radius: 3px; "
                            f"padding: 0.1rem 0.5rem; font-family: JetBrains Mono, monospace; "
                            f"font-size: 0.6rem; color: {T['--text-dim']};'>{t}</span>"
                            for t in tags
                        ])
                        st.markdown(
                            f"<div style='margin-top: 0.8rem; display: flex; "
                            f"gap: 0.3rem; flex-wrap: wrap;'>{tags_html}</div>",
                            unsafe_allow_html=True,
                        )

    with tab_generate:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1.5rem;'>
            GENERATE AI INCIDENT RESPONSE PLAYBOOK
        </div>
        """, unsafe_allow_html=True)

        threat_id = st.text_input(
            "THREAT ID",
            placeholder="T1486 — Data Encrypted for Impact",
            key="pb_threat_id",
        )
        context = st.text_area(
            "INCIDENT CONTEXT (optional)",
            placeholder="e.g. Ransomware detected on 3 Windows servers in finance department",
            height=100,
            key="pb_context",
        )
        tools_input = st.text_input(
            "AVAILABLE SOC TOOLS (comma separated)",
            placeholder="Splunk, CrowdStrike, Microsoft Sentinel",
            key="pb_tools",
        )

        if st.button("⟶ GENERATE PLAYBOOK", type="primary"):
            if not threat_id.strip():
                st.markdown(f"""
                <div style='background: {T["--warn-bg"]}; border: 1px solid {T["--warn-border"]};
                            border-left: 3px solid {T["--yellow"]}; border-radius: 6px;
                            padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                            font-size: 0.75rem; color: {T["--yellow"]};'>
                    ⚠ THREAT ID REQUIRED
                </div>
                """, unsafe_allow_html=True)
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
                    st.markdown(f"""
                    <div style='background: {T["--error-bg"]}; border: 1px solid {T["--error-border"]};
                                border-left: 3px solid {T["--red"]}; border-radius: 6px;
                                padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                                font-size: 0.8rem; color: {T["--red"]};'>
                        ⚠ {result["error"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: {T["--success-bg"]};
                                border: 1px solid {T["--success-border"]};
                                border-left: 3px solid {T["--green"]}; border-radius: 6px;
                                padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                                font-size: 0.75rem; color: {T["--green"]}; margin-bottom: 1.5rem;'>
                        ✓ PLAYBOOK #{result.get("id")} GENERATED SUCCESSFULLY
                    </div>
                    <div style='font-family: Rajdhani, sans-serif; font-size: 1.3rem;
                                font-weight: 700; color: {T["--text-primary"]};
                                margin-bottom: 0.3rem;'>{result.get("title")}</div>
                    <div style='font-family: Inter, sans-serif; font-size: 0.88rem;
                                color: {T["--text-secondary"]}; margin-bottom: 1.5rem;
                                line-height: 1.6;'>{result.get("objective")}</div>
                    """, unsafe_allow_html=True)

                    for step in result.get("steps", []):
                        st.markdown(step_card(step, T), unsafe_allow_html=True)