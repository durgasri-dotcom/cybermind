import streamlit as st

st.set_page_config(
    page_title="CyberMind",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

DARK = {
    "--bg-primary": "#0a0e1a",
    "--bg-secondary": "#0f1524",
    "--bg-card": "#131929",
    "--bg-card-hover": "#1a2235",
    "--border": "#1e2d4a",
    "--cyan": "#00d4ff",
    "--cyan-dim": "#00d4ff22",
    "--green": "#00ff88",
    "--red": "#ff3b3b",
    "--orange": "#ff8c00",
    "--yellow": "#ffd700",
    "--text-primary": "#e8edf5",
    "--text-secondary": "#8899b4",
    "--text-dim": "#4a5a7a",
    "--plot-bg": "#0f1524",
    "--tag-bg": "#1e2d4a",
    "--input-bg": "#0f1524",
    "--success-bg": "#0a1a0a",
    "--success-border": "#00ff8844",
    "--error-bg": "#1a0a0a",
    "--error-border": "#ff3b3b44",
    "--warn-bg": "#1a1500",
    "--warn-border": "#ffd70044",
}

LIGHT = {
    "--bg-primary": "#f4f6fb",
    "--bg-secondary": "#e8edf7",
    "--bg-card": "#ffffff",
    "--bg-card-hover": "#f0f4fb",
    "--border": "#c8d4e8",
    "--cyan": "#1a56db",
    "--cyan-dim": "#1a56db22",
    "--green": "#057a55",
    "--red": "#c81e1e",
    "--orange": "#b45309",
    "--yellow": "#92400e",
    "--text-primary": "#111928",
    "--text-secondary": "#374151",
    "--text-dim": "#6b7280",
    "--plot-bg": "#f4f6fb",
    "--tag-bg": "#e1e8f5",
    "--input-bg": "#f9fafb",
    "--success-bg": "#f0fdf4",
    "--success-border": "#057a5544",
    "--error-bg": "#fef2f2",
    "--error-border": "#c81e1e44",
    "--warn-bg": "#fffbeb",
    "--warn-border": "#92400e44",
}


def get_css(T: dict) -> str:
    vars_css = "\n".join([f"    {k}: {v};" for k, v in T.items()])
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap');

:root {{
{vars_css}
}}

html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}}

[data-testid="stSidebar"] {{
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}}

[data-testid="stSidebar"] * {{
    color: var(--text-primary) !important;
}}

section[data-testid="stSidebarContent"] {{
    padding: 1.5rem 1rem;
}}

h1, h2, h3 {{
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.05em;
    color: var(--text-primary) !important;
}}

.stRadio label {{
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.95rem !important;
    color: var(--text-secondary) !important;
    padding: 0.4rem 0 !important;
    cursor: pointer;
}}

.stRadio label:hover {{ color: var(--cyan) !important; }}

div[data-testid="metric-container"] {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 1rem 1.2rem !important;
}}

div[data-testid="metric-container"] label {{
    color: var(--text-secondary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase;
}}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: var(--cyan) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}}

.stButton button {{
    background: transparent !important;
    border: 1px solid var(--cyan) !important;
    color: var(--cyan) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase;
    border-radius: 4px !important;
    transition: all 0.2s !important;
}}

.stButton button:hover {{
    background: var(--cyan) !important;
    color: var(--bg-primary) !important;
}}

.stButton button[kind="primary"] {{
    background: var(--cyan) !important;
    color: var(--bg-primary) !important;
    font-weight: 700 !important;
}}

.stButton button[kind="primary"]:hover {{
    background: transparent !important;
    color: var(--cyan) !important;
}}

.stTextInput input, .stTextArea textarea {{
    background: var(--input-bg) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}}

.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 1px var(--cyan-dim) !important;
}}

.stTextInput input::placeholder, .stTextArea textarea::placeholder {{
    color: var(--text-dim) !important;
    font-style: italic;
}}

.stTextInput label, .stTextArea label, .stSelectbox label {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}}

div[data-baseweb="select"] > div {{
    background: var(--input-bg) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 4px !important;
}}

div[data-baseweb="select"] span {{
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}}

div[data-baseweb="popover"] li {{
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}}

div[data-baseweb="popover"] li:hover {{
    background: var(--cyan-dim) !important;
    color: var(--cyan) !important;
}}

.stSlider [data-baseweb="slider"] div[role="slider"] {{
    background: var(--cyan) !important;
    border-color: var(--cyan) !important;
}}

.stSlider [data-baseweb="slider"] div[data-testid="stSliderTrackFill"] {{
    background: var(--cyan) !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--text-secondary) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase;
    border: none !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 0.85rem !important;
}}

.stTabs [aria-selected="true"] {{
    color: var(--cyan) !important;
    border-bottom: 2px solid var(--cyan) !important;
}}

.stExpander {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    margin-bottom: 0.5rem !important;
}}

.stExpander summary, .stExpander summary p {{
    color: var(--text-primary) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
}}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {{
    color: var(--text-primary) !important;
}}

hr {{ border-color: var(--border) !important; }}

.stCaption, .stCaption p {{
    color: var(--text-secondary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
}}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--cyan); }}
</style>
"""


st.markdown(get_css(DARK if st.session_state.theme == "dark" else LIGHT),
            unsafe_allow_html=True)

from src.dashboard.tabs import alerts, analytics, cve_intel, entity_graph, overview, playbooks, threat_intel

TABS = {
    "Overview": ("🛡️", overview),
    "Threat Intel": ("🔍", threat_intel),
    "CVE Intel": ("🔴", cve_intel),
    "Alerts": ("🚨", alerts),
    "Playbooks": ("📋", playbooks),
    "Entity Graph": ("🕸️", entity_graph),
    "Analytics": ("📊", analytics),
}


def main():
    theme = st.session_state.theme
    T = DARK if theme == "dark" else LIGHT
    is_dark = theme == "dark"

    # ── Top right theme toggle ─────────────────────────────────────────────
    _, toggle_col = st.columns([9, 1])
    with toggle_col:
        label = "☀ LIGHT" if is_dark else "◑ DARK"
        if st.button(label, key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()

    # ── Sidebar ────────────────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style='margin-bottom: 1.5rem;'>
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.6rem; font-weight: 700;
                    color: {T["--cyan"]}; letter-spacing: 0.15em; text-transform: uppercase;'>
            ⬡ CYBERMIND
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.2em; text-transform: uppercase;
                    margin-top: 0.2rem;'>
            AI THREAT INTELLIGENCE
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(f"""
    <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                color: {T["--text-dim"]}; letter-spacing: 0.15em; text-transform: uppercase;
                margin-bottom: 0.5rem;'>NAVIGATION</div>
    """, unsafe_allow_html=True)

    selected = st.sidebar.radio(
        "nav",
        list(TABS.keys()),
        format_func=lambda x: f"{TABS[x][0]}  {x}",
        label_visibility="collapsed",
    )

    st.sidebar.markdown(f"""
    <hr style='border-color: {T["--border"]}; margin: 1.5rem 0;'>
    <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                color: {T["--text-dim"]};'>
        <div>v1.0.0 · MITRE ATT&CK</div>
        <div style='margin-top: 0.3rem;'>LLaMA 3.3 · FAISS · RAG</div>
        <div style='margin-top: 0.8rem; color: {T["--green"]};'>● OPERATIONAL</div>
    </div>
    """, unsafe_allow_html=True)

    TABS[selected][1].render(T)


if __name__ == "__main__":
    main()