import streamlit as st

st.set_page_config(
    page_title="CyberMind",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.dashboard.tabs import overview, threat_intel, alerts, playbooks, entity_graph

TABS = {
    "Overview": overview,
    "Threat Intel": threat_intel,
    "Alerts": alerts,
    "Playbooks": playbooks,
    "Entity Graph": entity_graph,
}

def main():
    st.sidebar.image("https://img.icons8.com/color/96/cyber-security.png", width=60)
    st.sidebar.title("CyberMind")
    st.sidebar.caption("AI-Powered Threat Intelligence Platform")
    st.sidebar.divider()

    selected = st.sidebar.radio("Navigate", list(TABS.keys()), label_visibility="collapsed")

    st.sidebar.divider()
    st.sidebar.caption("v1.0.0 · Powered by LLaMA 3.1")

    TABS[selected].render()


if __name__ == "__main__":
    main()