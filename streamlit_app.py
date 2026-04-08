import sys
from pathlib import Path
from tracemalloc import start

sys.path.insert(0, str(Path(__file__).parent))

import datetime
import math
import time

import plotly.graph_objects as go
import streamlit as st

BACKEND_URL = "https://cybermind-0y0t.onrender.com/api/v1"
API_KEY = st.secrets.get("CYBERMIND_API_KEY", "cybermind-dev-key-change-in-prod")

st.set_page_config(
    page_title="CyberMind",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "alerts" not in st.session_state:
    st.session_state.alerts = []
if "playbooks" not in st.session_state:
    st.session_state.playbooks = []
if "entities" not in st.session_state:
    st.session_state.entities = []

DARK = {
    "--bg-primary": "#0a0e1a",
    "--bg-secondary": "#0f1524",
    "--bg-card": "#131929",
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
:root {{ {vars_css} }}
html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif; color: var(--text-primary);
}}
[data-testid="stSidebar"] {{
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--text-primary) !important; }}
h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif !important; color: var(--text-primary) !important; }}
.stButton button {{
    background: transparent !important; border: 1px solid var(--cyan) !important;
    color: var(--cyan) !important; font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important; letter-spacing: 0.1em !important;
    text-transform: uppercase; border-radius: 4px !important; transition: all 0.2s !important;
}}
.stButton button:hover {{ background: var(--cyan) !important; color: var(--bg-primary) !important; }}
.stButton button[kind="primary"] {{ background: var(--cyan) !important; color: var(--bg-primary) !important; font-weight: 700 !important; }}
.stButton button[kind="primary"]:hover {{ background: transparent !important; color: var(--cyan) !important; }}
.stTextInput input, .stTextArea textarea {{
    background: var(--input-bg) !important; border: 1px solid var(--border) !important;
    color: var(--text-primary) !important; border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.85rem !important;
}}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{
    color: var(--text-dim) !important; font-style: italic;
}}
.stTextInput label, .stTextArea label, .stSelectbox label {{
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.7rem !important;
    letter-spacing: 0.1em !important; text-transform: uppercase; color: var(--text-secondary) !important;
}}
div[data-baseweb="select"] > div {{
    background: var(--input-bg) !important; border: 1px solid var(--border) !important;
    color: var(--text-primary) !important; border-radius: 4px !important;
}}
div[data-baseweb="select"] span {{ color: var(--text-primary) !important; font-family: 'JetBrains Mono', monospace !important; }}
div[data-baseweb="popover"] li {{ background: var(--bg-card) !important; color: var(--text-primary) !important; font-family: 'JetBrains Mono', monospace !important; }}
div[data-baseweb="popover"] li:hover {{ background: var(--cyan-dim) !important; color: var(--cyan) !important; }}
.stTabs [data-baseweb="tab-list"] {{ background: transparent !important; border-bottom: 1px solid var(--border) !important; }}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important; color: var(--text-secondary) !important;
    font-family: 'Rajdhani', sans-serif !important; font-weight: 600 !important;
    letter-spacing: 0.08em !important; text-transform: uppercase; border: none !important;
    padding: 0.6rem 1.2rem !important; font-size: 0.85rem !important;
}}
.stTabs [aria-selected="true"] {{ color: var(--cyan) !important; border-bottom: 2px solid var(--cyan) !important; }}
.stExpander {{ background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 6px !important; margin-bottom: 0.5rem !important; }}
.stExpander summary, .stExpander summary p {{ color: var(--text-primary) !important; font-family: 'Rajdhani', sans-serif !important; font-weight: 600 !important; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ color: var(--text-primary) !important; }}
hr {{ border-color: var(--border) !important; }}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--cyan); }}
</style>
"""


@st.cache_resource()
def load_services():
    from src.backend.services.llm_service import get_llm_service
    llm_svc = get_llm_service()
    return None, None, llm_svc


def status_card(label: str, value: str, color: str, T: dict):
    return f"""
    <div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};
    border-top:3px solid {color};border-radius:8px;padding:1.2rem 1.4rem;'>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};
    letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>
    <div style='font-family:Rajdhani,sans-serif;font-size:1.8rem;font-weight:700;color:{color};'>{value}</div>
    </div>"""


TEAM_CONFIG = {
    "SOC Tier 1":    ("--cyan",   "◈"),
    "SOC Tier 2":    ("--cyan",   "◉"),
    "IR Team":       ("--orange", "⬡"),
    "Management":    ("--text-secondary", "◇"),
    "IT Operations": ("--green",  "⬢"),
}

ENTITY_TYPE_COLORS = {
    "threat_actor":   "--red",
    "malware":        "--orange",
    "tool":           "--yellow",
    "campaign":       "--cyan",
    "infrastructure": "--text-secondary",
}

ENTITY_ICONS = {
    "threat_actor": "🎭",
    "malware": "🦠",
    "tool": "🔧",
    "campaign": "📡",
    "infrastructure": "🖧",
}


def step_card(step: dict, T: dict) -> str:
    team = step.get("responsible_team", "SOC Tier 1")
    color_key, icon = TEAM_CONFIG.get(team, ("--text-secondary", "○"))
    color = T[color_key]
    tools = step.get("tools", [])
    tools_str = " · ".join(tools) if tools else "—"
    notes = step.get("notes", "")
    return f"""
    <div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};
    border-left:3px solid {color};border-radius:6px;padding:0.9rem 1rem;margin-bottom:0.5rem;'>
    <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
    <div style='flex:1;'>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{color};letter-spacing:0.1em;margin-bottom:0.3rem;'>STEP {step["step_number"]:02d}</div>
    <div style='font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:600;color:{T["--text-primary"]};margin-bottom:0.4rem;'>{step["action"]}</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};'>TOOLS: {tools_str}</div>
    {f'<div style="font-family:Inter,sans-serif;font-size:0.8rem;color:{T["--text-secondary"]};margin-top:0.4rem;line-height:1.5;">{notes[:200]}</div>' if notes else ""}
    </div>
    <div style='text-align:right;flex-shrink:0;margin-left:1rem;'>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{color};'>{icon} {team}</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};margin-top:0.3rem;'>~{step.get("estimated_minutes",30)} min</div>
    </div></div></div>"""


def render_overview(T: dict, rag_svc, llm_svc):
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>THREAT INTELLIGENCE OVERVIEW</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>REAL-TIME PLATFORM STATUS · MITRE ATT&CK · NVD CVE</div>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(status_card("PLATFORM STATUS", "OPERATIONAL", T["--green"], T), unsafe_allow_html=True)
    with col2: st.markdown(status_card("VECTOR STORE", "READY", T["--green"], T), unsafe_allow_html=True)
    with col3: st.markdown(status_card("THREATS INDEXED", "3,024", T["--cyan"], T), unsafe_allow_html=True)
    with col4: st.markdown(status_card("LLM ENGINE", "LLAMA 3.3", T["--cyan"], T), unsafe_allow_html=True)

    st.markdown(f"<div style='margin:2rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>THREAT DISTRIBUTION BY SEVERITY</div>", unsafe_allow_html=True)
        SEV_COLORS = {"critical": T["--red"], "high": T["--orange"], "medium": T["--yellow"], "low": T["--green"], "unknown": T["--text-dim"]}
        by_sev = {s: 0 for s in SEV_COLORS}
        filtered = {k: v for k, v in by_sev.items() if v > 0}
        if not filtered:
            import json
            from configs.settings import settings as cfg
            p = Path(cfg.mitre_gold_path)
            if p.exists():
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                for t in data:
                    sev = t.get("severity", "unknown")
                    by_sev[sev] = by_sev.get(sev, 0) + 1
                filtered = {k: v for k, v in by_sev.items() if v > 0}
        if filtered:
            labels = list(filtered.keys())
            values = list(filtered.values())
            colors = [SEV_COLORS.get(s, T["--text-dim"]) for s in labels]
            fig = go.Figure(go.Pie(
                labels=[s.upper() for s in labels], values=values,
                marker=dict(colors=colors, line=dict(color=T["--bg-primary"], width=2)),
                hole=0.6, textfont=dict(family="JetBrains Mono", size=11, color=T["--text-primary"]),
                hovertemplate="<b>%{label}</b><br>%{value} threats<br>%{percent}<extra></extra>",
            ))
            fig.add_annotation(text=f"<b>{sum(values):,}</b><br><span style='font-size:10px'>TOTAL</span>",
                x=0.5, y=0.5, font=dict(family="Rajdhani", size=22, color=T["--cyan"]), showarrow=False)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", color=T["--text-secondary"]),
                showlegend=True, legend=dict(font=dict(family="JetBrains Mono", size=10, color=T["--text-secondary"]), bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=20, b=20, l=20, r=20), height=300)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>PLATFORM SERVICES</div>", unsafe_allow_html=True)
        services = [
            ("RAG", True, "vectors: 3,024"),
            ("LLM", True, "groq · llama-3.3-70b"),
            ("EMBEDDINGS", True, "all-MiniLM-L6-v2"),
            ("VECTOR BACKEND", True, "faiss"),
        ]
        for svc, ready, detail in services:
            dot = T["--green"] if ready else T["--red"]
            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-radius:6px;padding:0.7rem 1rem;margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;'>
            <div style='display:flex;align-items:center;gap:0.6rem;'><span style='color:{dot};font-size:0.7rem;'>●</span>
            <span style='font-family:Rajdhani,sans-serif;font-weight:600;color:{T["--text-primary"]};text-transform:uppercase;font-size:0.85rem;'>{svc}</span></div>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};'>{detail}</div></div>""", unsafe_allow_html=True)

    st.markdown(f"<div style='margin:2rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>INTELLIGENCE STACK</div>", unsafe_allow_html=True)

    from configs.settings import settings as cfg
    items = [("DATA SOURCES", "MITRE ATT&CK + NVD CVE"), ("EMBEDDING MODEL", "all-MiniLM-L6-v2"),
             ("VECTOR BACKEND", "FAISS" if not cfg.use_pinecone else "Pinecone"), ("RAG CHUNKS", "3,024")]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-radius:8px;padding:1rem 1.2rem;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.4rem;'>{label}</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:600;color:{T["--text-secondary"]};'>{value}</div></div>""", unsafe_allow_html=True)


def render_threat_intel(T: dict, rag_svc, llm_svc):
    import httpx
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>THREAT INTELLIGENCE Q&A</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>RAG-POWERED ANALYSIS · MITRE ATT&CK · LLAMA 3.3 70B</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-radius:8px;padding:1.5rem;margin-bottom:1.5rem;'>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.8rem;'>SAMPLE QUERIES</div>
    <div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1rem;'>
    {"".join([f"<span style='background:{T['--cyan-dim']};border:1px solid {T['--cyan']}44;border-radius:4px;padding:0.3rem 0.7rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--cyan']};letter-spacing:0.05em;'>{q}</span>" for q in ["How does APT29 achieve persistence?", "Explain T1059.001 PowerShell techniques", "Common ransomware lateral movement TTPs", "Detect credential dumping with Splunk"]])}
    </div></div>""", unsafe_allow_html=True)

    query = st.text_area("ANALYST QUERY", placeholder="e.g. How does APT29 achieve persistence on Windows?", height=90, key="intel_query")
    col1, col2 = st.columns([4, 1])
    with col1:
        top_k = st.slider("CONTEXT CHUNKS TO RETRIEVE", min_value=1, max_value=15, value=5, key="intel_topk")
    with col2:
        analyze = st.button("⟶ ANALYZE", type="primary", use_container_width=True)

    if analyze and query.strip():
        start = time.perf_counter()
        try:
            r = httpx.post(
                f"{BACKEND_URL}/intel/query",
                json={"query": query.strip(), "top_k": top_k},
                headers={"X-API-Key": API_KEY},
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            st.error(f"Backend error: {e}")
            return

        chunks = data.get("retrieved_chunks", [])
        sources = data.get("sources", [])
        similar_threats = data.get("similar_threats", [])
        analysis = data.get("analysis", "")
        elapsed = (time.perf_counter() - start) * 1000

        c1, c2, c3 = st.columns(3)
        for col, label, value, color in [
            (c1, "LATENCY", f"{elapsed:.0f}ms", T["--green"] if elapsed < 5000 else T["--yellow"]),
            (c2, "CHUNKS RETRIEVED", str(len(chunks)), T["--cyan"]),
            (c3, "RAG STATUS", "READY", T["--green"]),
        ]:
            with col:
                st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-top:3px solid {color};border-radius:6px;padding:0.8rem 1rem;text-align:center;'>
                <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.3rem;'>{label}</div>
                <div style='font-family:Rajdhani,sans-serif;font-size:1.4rem;font-weight:700;color:{color};'>{value}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>INTELLIGENCE REPORT</div>", unsafe_allow_html=True)
        st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-left:3px solid {T["--cyan"]};border-radius:8px;padding:1.5rem;line-height:1.8;font-family:Inter,sans-serif;font-size:0.9rem;color:{T["--text-primary"]};white-space:pre-wrap;'>{analysis}</div>""", unsafe_allow_html=True)

        if sources:
            st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>MITRE SOURCES</div>", unsafe_allow_html=True)
            for source in sources:
                st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T['--cyan']};margin-bottom:0.3rem;'>▸ {source}</div>", unsafe_allow_html=True)

        if similar_threats:
            st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>SIMILAR THREATS RETRIEVED</div>", unsafe_allow_html=True)
            for threat in similar_threats:
                tid = threat.get("threat_id", "unknown")
                name = threat.get("name", tid)
                score = threat.get("score", 0.0)
                preview = threat.get("chunk_preview", "")
                sc = T["--green"] if score > 0.6 else T["--yellow"] if score > 0.4 else T["--text-dim"]
                st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-radius:6px;padding:0.8rem 1rem;margin-bottom:0.4rem;'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                <span style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--cyan"]};'>{tid}</span>
                <span style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{sc};'>{score:.4f}</span></div>
                <div style='font-family:Rajdhani,sans-serif;font-size:0.95rem;color:{T["--text-primary"]};font-weight:600;margin-top:0.3rem;'>{name}</div>
                <div style='font-family:Inter,sans-serif;font-size:0.75rem;color:{T["--text-dim"]};margin-top:0.3rem;'>{preview}</div>
                </div>""", unsafe_allow_html=True)

        if chunks:
            with st.expander("◈ VIEW RAW CONTEXT CHUNKS"):
                for i, chunk in enumerate(chunks, 1):
                    st.markdown(f"""<div style='background:{T["--input-bg"]};border:1px solid {T["--border"]};border-radius:4px;padding:0.8rem;margin-bottom:0.5rem;'>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--cyan"]};letter-spacing:0.1em;margin-bottom:0.4rem;'>CHUNK {i:02d}</div>
                    <div style='font-family:Inter,sans-serif;font-size:0.8rem;color:{T["--text-secondary"]};line-height:1.6;'>{chunk}</div></div>""", unsafe_allow_html=True)

    elif analyze:
        st.markdown(f"""<div style='background:{T["--warn-bg"]};border:1px solid {T["--warn-border"]};border-left:3px solid {T["--yellow"]};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--yellow"]};'>⚠ QUERY REQUIRED — Enter a threat intelligence question</div>""", unsafe_allow_html=True)

def render_alerts(T: dict, llm_svc):
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>SECURITY ALERTS</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>ALERT TRIAGE · AI-ASSISTED ANALYSIS · SOC WORKFLOW</div>
    </div>""", unsafe_allow_html=True)

    tab_list, tab_create = st.tabs(["ALERT FEED", "CREATE ALERT"])
    P_COLORS = {"P1": T["--red"], "P2": T["--orange"], "P3": T["--yellow"], "P4": T["--green"]}
    P_LABELS = {"P1": "CRITICAL", "P2": "HIGH", "P3": "MEDIUM", "P4": "LOW"}
    S_ICONS = {"open": "●", "in_progress": "◑", "resolved": "✓", "false_positive": "✕"}

    with tab_list:
        col1, col2 = st.columns([3, 1])
        with col1:
            status_filter = st.selectbox("FILTER BY STATUS", ["All", "open", "in_progress", "resolved", "false_positive"], key="alert_filter")
        with col2:
            st.markdown("<div style='margin-top:1.8rem;'></div>", unsafe_allow_html=True)
            if st.button("↻ REFRESH", use_container_width=True):
                st.rerun()

        alerts = st.session_state.alerts
        if status_filter != "All":
            alerts = [a for a in alerts if a.get("status") == status_filter]

        st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:1rem;'>{len(alerts)} ALERT(S) FOUND</div>", unsafe_allow_html=True)

        if not alerts:
            st.markdown(f"<div style='background:{T['--bg-card']};border:1px solid {T['--border']};border-radius:8px;padding:2rem;text-align:center;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{T['--text-dim']};'>NO ALERTS FOUND</div>", unsafe_allow_html=True)
        else:
            for alert in reversed(alerts):
                priority = alert.get("priority", "P3")
                status = alert.get("status", "open")
                p_color = P_COLORS.get(priority, T["--text-dim"])
                p_label = P_LABELS.get(priority, priority)
                s_icon = S_ICONS.get(status, "?")
                with st.expander(f"[{p_label}]  {alert['title']}"):
                    st.markdown(f"""<div style='display:flex;gap:0.6rem;margin-bottom:1rem;flex-wrap:wrap;align-items:center;'>
                    <span style='background:{p_color}22;border:1px solid {p_color}55;border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{p_color};letter-spacing:0.08em;'>{priority} · {p_label}</span>
                    <span style='background:{T["--tag-bg"]};border:1px solid {T["--border"]};border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-secondary"]};letter-spacing:0.08em;'>{s_icon} {status.upper()}</span>
                    <span style='background:{T["--cyan-dim"]};border:1px solid {T["--cyan"]}44;border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--cyan"]};letter-spacing:0.08em;'>{alert.get("threat_id")}</span>
                    </div>
                    <div style='font-family:Inter,sans-serif;font-size:0.88rem;color:{T["--text-secondary"]};margin-bottom:1rem;line-height:1.6;'>{alert.get("description","")}</div>""", unsafe_allow_html=True)

                    if alert.get("indicators"):
                        st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:0.5rem;'>INDICATORS OF COMPROMISE</div>", unsafe_allow_html=True)
                        for ioc in alert["indicators"]:
                            st.markdown(f"<div style='background:{T['--input-bg']};border:1px solid {T['--border']};border-left:2px solid {T['--orange']};border-radius:4px;padding:0.3rem 0.7rem;margin-bottom:0.3rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T['--orange']};'>{ioc}</div>", unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("⟶ AI TRIAGE", key=f"triage_{alert['id']}"):
                            with st.spinner("Analyzing..."):
                                analysis, _ = llm_svc.triage_alert(
                                    alert_title=alert["title"],
                                    alert_description=alert["description"],
                                    threat_context=f"Threat ID: {alert['threat_id']}",
                                    indicators=alert.get("indicators", []),
                                )
                            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--cyan"]}44;border-left:3px solid {T["--cyan"]};border-radius:6px;padding:1rem;margin-top:0.5rem;font-family:Inter,sans-serif;font-size:0.85rem;color:{T["--text-primary"]};line-height:1.6;'>{analysis}</div>""", unsafe_allow_html=True)
                    with col_b:
                        new_status = st.selectbox("UPDATE STATUS", ["open", "in_progress", "resolved", "false_positive"], key=f"status_{alert['id']}")
                    with col_c:
                        st.markdown("<div style='margin-top:1.8rem;'></div>", unsafe_allow_html=True)
                        if st.button("UPDATE", key=f"update_{alert['id']}"):
                            for a in st.session_state.alerts:
                                if a["id"] == alert["id"]:
                                    a["status"] = new_status
                            st.rerun()

    with tab_create:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.5rem;'>CREATE SECURITY ALERT</div>", unsafe_allow_html=True)
        threat_id = st.text_input("THREAT ID", placeholder="T1059.001", key="new_threat_id")
        title = st.text_input("TITLE", placeholder="Suspicious PowerShell execution detected", key="new_title")
        description = st.text_area("DESCRIPTION", height=100, key="new_description")
        priority = st.selectbox("PRIORITY", ["P1", "P2", "P3", "P4"], key="new_priority")
        source_ip = st.text_input("SOURCE IP (optional)", key="new_source_ip")
        target_asset = st.text_input("TARGET ASSET (optional)", key="new_target_asset")
        indicators = st.text_area("INDICATORS — one per line", height=80, key="new_indicators")

        if st.button("⟶ CREATE ALERT", type="primary"):
            if not all([threat_id, title, description]):
                st.markdown(f"<div style='background:{T['--warn-bg']};border:1px solid {T['--warn-border']};border-left:3px solid {T['--yellow']};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T['--yellow']};'>⚠ THREAT ID, TITLE, AND DESCRIPTION REQUIRED</div>", unsafe_allow_html=True)
            else:
                st.session_state.alerts.append({
                    "id": len(st.session_state.alerts) + 1,
                    "threat_id": threat_id, "title": title,
                    "description": description, "priority": priority,
                    "status": "open",
                    "source_ip": source_ip or None,
                    "target_asset": target_asset or None,
                    "indicators": [i.strip() for i in indicators.splitlines() if i.strip()],
                    "triggered_at": datetime.datetime.now().isoformat(),
                })
                st.markdown(f"<div style='background:{T['--success-bg']};border:1px solid {T['--success-border']};border-left:3px solid {T['--green']};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T['--green']};'>✓ ALERT #{len(st.session_state.alerts)} CREATED SUCCESSFULLY</div>", unsafe_allow_html=True)
                st.rerun()


def render_playbooks(T: dict, rag_svc, llm_svc):
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>INCIDENT RESPONSE PLAYBOOKS</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>AI-GENERATED · MITRE ATT&CK · STRUCTURED RESPONSE WORKFLOWS</div>
    </div>""", unsafe_allow_html=True)

    tab_list, tab_generate = st.tabs(["SAVED PLAYBOOKS", "GENERATE PLAYBOOK"])

    with tab_list:
        if st.button("↻ REFRESH", use_container_width=False):
            st.rerun()
        playbooks = st.session_state.playbooks
        st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:1rem;'>{len(playbooks)} PLAYBOOK(S) AVAILABLE</div>", unsafe_allow_html=True)

        if not playbooks:
            st.markdown(f"<div style='background:{T['--bg-card']};border:1px solid {T['--border']};border-radius:8px;padding:2rem;text-align:center;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{T['--text-dim']};'>NO PLAYBOOKS — Generate one from the Generate tab</div>", unsafe_allow_html=True)
        else:
            for pb in reversed(playbooks):
                with st.expander(f"⬡  {pb.get('title')} — {pb.get('threat_id')}"):
                    st.markdown(f"""<div style='display:flex;gap:0.6rem;margin-bottom:1rem;flex-wrap:wrap;'>
                    <span style='background:{T["--cyan-dim"]};border:1px solid {T["--cyan"]}44;border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--cyan"]};'>{pb.get("threat_id")}</span>
                    <span style='background:{T["--success-bg"]};border:1px solid {T["--success-border"]};border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--green"]};'>ACTIVE</span>
                    <span style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};'>{pb.get("generated_at","")[:19].replace("T"," ")} UTC</span>
                    </div>
                    <div style='font-family:Inter,sans-serif;font-size:0.88rem;color:{T["--text-secondary"]};margin-bottom:1.2rem;line-height:1.6;'>{pb.get("objective","")}</div>""", unsafe_allow_html=True)
                    for step in pb.get("steps", []):
                        st.markdown(step_card(step, T), unsafe_allow_html=True)
                    tags = pb.get("tags", [])
                    if tags:
                        tags_html = " ".join([f"<span style='background:{T['--tag-bg']};border-radius:3px;padding:0.1rem 0.5rem;font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T['--text-dim']};'>{t}</span>" for t in tags])
                        st.markdown(f"<div style='margin-top:0.8rem;display:flex;gap:0.3rem;flex-wrap:wrap;'>{tags_html}</div>", unsafe_allow_html=True)

    with tab_generate:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.5rem;'>GENERATE AI INCIDENT RESPONSE PLAYBOOK</div>", unsafe_allow_html=True)
        threat_id = st.text_input("THREAT ID", placeholder="T1486 — Data Encrypted for Impact", key="pb_threat_id")
        context = st.text_area("INCIDENT CONTEXT (optional)", placeholder="e.g. Ransomware detected on 3 Windows servers", height=100, key="pb_context")
        tools_input = st.text_input("AVAILABLE SOC TOOLS (comma separated)", placeholder="Splunk, CrowdStrike, Microsoft Sentinel", key="pb_tools")

        if st.button("⟶ GENERATE PLAYBOOK", type="primary"):
            if not threat_id.strip():
                st.markdown(f"<div style='background:{T['--warn-bg']};border:1px solid {T['--warn-border']};border-left:3px solid {T['--yellow']};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T['--yellow']};'>⚠ THREAT ID REQUIRED</div>", unsafe_allow_html=True)
            else:
                tools = [t.strip() for t in tools_input.split(",") if t.strip()]
                rag_context = []
                try:
                      _r = httpx.post(f"{BACKEND_URL}/intel/query", json={"query": f"incident response {threat_id} containment", "top_k": 3}, headers={"X-API-Key": API_KEY}, timeout=30)
                      rag_context = _r.json().get("retrieved_chunks", [])
                except Exception:
                      rag_context = []
                alert_context = context.strip()
                if rag_context:
                    alert_context += "\n\nRelevant context:\n" + "\n\n".join(rag_context[:2])
                with st.spinner("Generating playbook..."):
                    raw, _ = llm_svc.generate_playbook(
                        threat_id=threat_id.strip(), threat_name=threat_id.strip(),
                        alert_context=alert_context, available_tools=tools,
                    )
                from src.backend.routers.playbooks import _parse_steps
                steps = _parse_steps(raw)
                pb = {
                    "id": len(st.session_state.playbooks) + 1,
                    "threat_id": threat_id.strip(),
                    "title": f"IR Playbook: {threat_id.strip()}",
                    "objective": f"Contain, eradicate, and recover from {threat_id.strip()} incident",
                    "steps": [s.model_dump() for s in steps],
                    "tags": ["auto-generated", threat_id.strip()],
                    "generated_at": datetime.datetime.now().isoformat(),
                }
                st.session_state.playbooks.append(pb)
                st.markdown(f"""<div style='background:{T["--success-bg"]};border:1px solid {T["--success-border"]};border-left:3px solid {T["--green"]};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--green"]};margin-bottom:1.5rem;'>✓ PLAYBOOK #{pb["id"]} GENERATED SUCCESSFULLY</div>
                <div style='font-family:Rajdhani,sans-serif;font-size:1.3rem;font-weight:700;color:{T["--text-primary"]};margin-bottom:0.3rem;'>{pb["title"]}</div>
                <div style='font-family:Inter,sans-serif;font-size:0.88rem;color:{T["--text-secondary"]};margin-bottom:1.5rem;line-height:1.6;'>{pb["objective"]}</div>""", unsafe_allow_html=True)
                for step in steps:
                    st.markdown(step_card(step.model_dump(), T), unsafe_allow_html=True)


def render_entity_graph(T: dict, llm_svc):
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>ENTITY GRAPH</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>THREAT ACTORS · MALWARE · TOOLS · RELATIONSHIP MAPPING</div>
    </div>""", unsafe_allow_html=True)

    tab_graph, tab_list, tab_add = st.tabs(["RELATIONSHIP GRAPH", "ENTITY LIST", "ADD ENTITY"])

    with tab_graph:
        filter_col, _ = st.columns([2, 5])
        with filter_col:
            entity_type_filter = st.selectbox("FILTER BY TYPE", ["All", "threat_actor", "malware", "tool", "campaign", "infrastructure"], key="graph_filter")

        entities = st.session_state.entities
        if entity_type_filter != "All":
            entities = [e for e in entities if e.get("entity_type") == entity_type_filter]

        if not entities:
            st.markdown(f"<div style='background:{T['--bg-card']};border:1px solid {T['--border']};border-radius:8px;padding:3rem;text-align:center;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{T['--text-dim']};'>NO ENTITIES — Add entities from the Add Entity tab</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:0.8rem;'>{len(entities)} ENTITIES · NODE SIZE = TECHNIQUE COUNT · LINES = SHARED TECHNIQUES</div>", unsafe_allow_html=True)
            legend_cols = st.columns(5)
            for col, (etype, color_key) in zip(legend_cols, ENTITY_TYPE_COLORS.items()):
                with col:
                    st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T[color_key]};letter-spacing:0.05em;'>● {etype.replace('_',' ').upper()}</div>", unsafe_allow_html=True)

            n = len(entities)
            node_x, node_y, node_text, node_hover, node_colors, node_sizes = [], [], [], [], [], []
            for i, entity in enumerate(entities):
                angle = 2 * math.pi * i / max(n, 1)
                radius = 0.7 + (0.15 * (i % 3))
                x, y = radius * math.cos(angle), radius * math.sin(angle)
                node_x.append(x)
                node_y.append(y)
                node_text.append(entity["name"])
                node_hover.append(f"<b>{entity['name']}</b><br>{entity.get('entity_type','').upper()}<br>ID: {entity['entity_id']}<br>Techniques: {len(entity.get('associated_techniques', []))}")
                color_key = ENTITY_TYPE_COLORS.get(entity.get("entity_type", ""), "--text-secondary")
                node_colors.append(T[color_key])
                node_sizes.append(18 + len(entity.get("associated_techniques", [])) * 0.8)

            # ── build edges from shared techniques + explicit relationships ──
            pos_map = {entities[i]["entity_id"]: (node_x[i], node_y[i]) for i in range(len(entities))}
            edge_x_list, edge_y_list = [], []
            for ii, e1 in enumerate(entities):
                t1 = set(e1.get("associated_techniques", []))
                for jj, e2 in enumerate(entities):
                    if jj <= ii:
                        continue
                    shared = t1 & set(e2.get("associated_techniques", []))
                    if shared:
                        x1, y1 = pos_map[e1["entity_id"]]
                        x2, y2 = pos_map[e2["entity_id"]]
                        edge_x_list += [x1, x2, None]
                        edge_y_list += [y1, y2, None]
                for rel in e1.get("relationships", []):
                    tid = rel.get("target_entity_id")
                    if tid in pos_map:
                        x1, y1 = pos_map[e1["entity_id"]]
                        x2, y2 = pos_map[tid]
                        edge_x_list += [x1, x2, None]
                        edge_y_list += [y1, y2, None]

            edge_trace = go.Scatter(x=edge_x_list, y=edge_y_list, mode="lines",
                line=dict(width=1, color=T["--border"]), hoverinfo="none", opacity=0.6)
            node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text", text=node_text,
                textposition="top center", textfont=dict(family="Rajdhani", size=11, color=T["--text-secondary"]),
                hovertext=node_hover, hoverinfo="text",
                marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color=T["--bg-primary"])))
            fig = go.Figure(data=[edge_trace, node_trace])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=T["--plot-bg"],
                showlegend=False, height=500, margin=dict(t=20, b=20, l=20, r=20),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
            st.plotly_chart(fig, use_container_width=True)

    with tab_list:
        entities_all = st.session_state.entities
        if not entities_all:
            st.markdown(f"<div style='background:{T['--bg-card']};border:1px solid {T['--border']};border-radius:8px;padding:2rem;text-align:center;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{T['--text-dim']};'>NO ENTITIES YET</div>", unsafe_allow_html=True)
        else:
            for entity in entities_all:
                color_key = ENTITY_TYPE_COLORS.get(entity.get("entity_type", ""), "--text-secondary")
                color = T[color_key]
                icon = ENTITY_ICONS.get(entity.get("entity_type", ""), "?")
                with st.expander(f"{icon}  {entity['name']} — {entity.get('entity_type','').upper()}"):
                    st.markdown(f"""<div style='display:flex;gap:0.6rem;margin-bottom:1rem;'>
                    <span style='background:{color}22;border:1px solid {color}55;border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{color};'>{entity["entity_id"]}</span></div>
                    <div style='font-family:Inter,sans-serif;font-size:0.88rem;color:{T["--text-secondary"]};margin-bottom:1rem;line-height:1.6;'>{entity.get("description","")[:400]}</div>""", unsafe_allow_html=True)
                    techniques = entity.get("associated_techniques", [])
                    if techniques:
                        tags_html = " ".join([f"<span style='background:{T['--cyan-dim']};border:1px solid {T['--cyan']}33;border-radius:3px;padding:0.1rem 0.4rem;font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T['--cyan']};'>{t}</span>" for t in techniques[:10]])
                        st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:0.5rem;'>ASSOCIATED TECHNIQUES</div><div style='display:flex;gap:0.3rem;flex-wrap:wrap;margin-bottom:1rem;'>{tags_html}</div>", unsafe_allow_html=True)
                    if st.button("⟶ AI ENRICH", key=f"enrich_{entity['entity_id']}"):
                        with st.spinner("Generating threat profile..."):
                            profile, _ = llm_svc.generate_entity_profile(
                                entity_id=entity["entity_id"], entity_name=entity["name"],
                                entity_type=entity["entity_type"], description=entity["description"],
                                associated_techniques=entity.get("associated_techniques", []),
                            )
                        st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--cyan"]}44;border-left:3px solid {T["--cyan"]};border-radius:6px;padding:1rem;margin-top:0.5rem;font-family:Inter,sans-serif;font-size:0.88rem;color:{T["--text-primary"]};line-height:1.7;'>{profile}</div>""", unsafe_allow_html=True)

    with tab_add:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.5rem;'>ADD THREAT ENTITY</div>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a: entity_id = st.text_input("ENTITY ID", placeholder="G0007", key="ent_id")
        with col_b: name = st.text_input("NAME", placeholder="APT28", key="ent_name")
        entity_type = st.selectbox("TYPE", ["threat_actor", "malware", "tool", "campaign", "infrastructure"], key="ent_type")
        description = st.text_area("DESCRIPTION", height=100, key="ent_desc")
        col_c, col_d = st.columns(2)
        with col_c:
            aliases = st.text_input("ALIASES (comma separated)", placeholder="Fancy Bear, Sofacy", key="ent_aliases")
            sectors = st.text_input("TARGETED SECTORS", placeholder="Government, Defense", key="ent_sectors")
        with col_d:
            techniques = st.text_input("ASSOCIATED TECHNIQUES", placeholder="T1059, T1078, T1566", key="ent_techniques")
            countries = st.text_input("TARGETED COUNTRIES", placeholder="US, UK, Ukraine", key="ent_countries")

        if st.button("⟶ ADD ENTITY", type="primary"):
            if not all([entity_id, name, description]):
                st.markdown(f"<div style='background:{T['--warn-bg']};border:1px solid {T['--warn-border']};border-left:3px solid {T['--yellow']};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T['--yellow']};'>⚠ ENTITY ID, NAME, AND DESCRIPTION REQUIRED</div>", unsafe_allow_html=True)
            else:
                st.session_state.entities.append({
                    "entity_id": entity_id.strip(), "name": name.strip(),
                    "entity_type": entity_type, "description": description.strip(),
                    "aliases": [a.strip() for a in aliases.split(",") if a.strip()],
                    "associated_techniques": [t.strip() for t in techniques.split(",") if t.strip()],
                    "targeted_sectors": [s.strip() for s in sectors.split(",") if s.strip()],
                    "targeted_countries": [c.strip() for c in countries.split(",") if c.strip()],
                })
                st.markdown(f"<div style='background:{T['--success-bg']};border:1px solid {T['--success-border']};border-left:3px solid {T['--green']};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T['--green']};'>✓ ENTITY '{name.upper()}' ADDED SUCCESSFULLY</div>", unsafe_allow_html=True)
                st.rerun()

def render_sigma(T: dict):
    import httpx
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>SIGMA RULE GENERATOR</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>AI-GENERATED DETECTION RULES · MITRE ATT&CK · SIEM-READY YAML</div>
    </div>""", unsafe_allow_html=True)

    query = st.text_area("THREAT QUERY", placeholder="e.g. PowerShell execution and credential dumping", height=90, key="sigma_query")
    generate = st.button("⟶ GENERATE SIGMA RULE", type="primary")

    if generate and query.strip():
        with st.spinner("Generating Sigma detection rule..."):
            try:
                r = httpx.post(
                    f"{BACKEND_URL}/intel/sigma",
                    json={"query": query.strip()},
                    headers={"X-API-Key": API_KEY},
                    timeout=60,
                )
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                st.error(f"Backend error: {e}")
                return

        st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-top:3px solid {T["--cyan"]};border-radius:6px;padding:0.8rem 1rem;text-align:center;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-bottom:0.3rem;'>THREAT ID</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:1.2rem;font-weight:700;color:{T["--cyan"]};'>{data.get("threat_id", "—")}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-top:3px solid {T["--green"]};border-radius:6px;padding:0.8rem 1rem;text-align:center;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-bottom:0.3rem;'>THREAT NAME</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;color:{T["--green"]};'>{data.get("threat_name", "—")[:30]}</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-top:3px solid {T["--yellow"]};border-radius:6px;padding:0.8rem 1rem;text-align:center;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-bottom:0.3rem;'>LATENCY</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:1.2rem;font-weight:700;color:{T["--yellow"]};'>{data.get("latency_ms", 0):.0f}ms</div></div>""", unsafe_allow_html=True)

        st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)

        techniques = data.get("mitre_techniques", [])
        if techniques:
            tags_html = " ".join([f"<span style='background:{T['--cyan-dim']};border:1px solid {T['--cyan']}44;border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--cyan']};'>{t}</span>" for t in techniques])
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:0.5rem;'>MITRE TECHNIQUES</div><div style='display:flex;gap:0.4rem;flex-wrap:wrap;margin-bottom:1.5rem;'>{tags_html}</div>", unsafe_allow_html=True)

        sigma_rule = data.get("sigma_rule", "")
        sigma_clean = sigma_rule.replace("```yml", "").replace("```yaml", "").replace("```", "").strip()

        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>GENERATED SIGMA RULE</div>", unsafe_allow_html=True)
        st.markdown(f"""<div style='background:{T["--input-bg"]};border:1px solid {T["--border"]};border-left:3px solid {T["--cyan"]};border-radius:8px;padding:1.5rem;font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{T["--text-secondary"]};line-height:1.8;white-space:pre-wrap;overflow-x:auto;'>{sigma_clean}</div>""", unsafe_allow_html=True)
        st.markdown(f"""<div style='background:{T["--success-bg"]};border:1px solid {T["--success-border"]};border-left:3px solid {T["--green"]};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--green"]};margin-top:1rem;'>
        ✓ SIEM-READY — Deploy directly to Splunk, Microsoft Sentinel, Elastic SIEM, or any Sigma-compatible platform</div>""", unsafe_allow_html=True)

    elif generate:
        st.markdown(f"""<div style='background:{T["--warn-bg"]};border:1px solid {T["--warn-border"]};border-left:3px solid {T["--yellow"]};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--yellow"]};'>⚠ QUERY REQUIRED</div>""", unsafe_allow_html=True)
def render_cve_intel(T: dict):
    import httpx
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>CVE INTELLIGENCE</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>LIVE NVD FEED · CVSS SCORING · MITRE ATT&CK MAPPING</div>
    </div>""", unsafe_allow_html=True)

    stats = None
    cves = []
    backend_online = False
    try:
        r = httpx.get(f"{BACKEND_URL}/cves/stats", timeout=15)
        if r.status_code == 200:
            stats = r.json()
            backend_online = True
        r2 = httpx.get(f"{BACKEND_URL}/cves", params={"limit": 50}, timeout=15)
        if r2.status_code == 200:
            cves = r2.json().get("cves", [])
    except Exception:
        pass

    if not backend_online:
        st.markdown(f"""
        <div style='background:{T["--warn-bg"]};border:1px solid {T["--warn-border"]};
        border-left:3px solid {T["--yellow"]};border-radius:8px;padding:1.2rem 1.5rem;
        margin-bottom:1.5rem;'>
        <div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:700;
        color:{T["--yellow"]};margin-bottom:0.4rem;'>⏳ BACKEND WARMING UP</div>
        <div style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--text-secondary"]};line-height:1.6;'>
        The CyberMind backend is starting up on Render (free tier cold start ~30s).<br>
        Click refresh in a moment to load live CVE data from NVD.
        </div></div>""", unsafe_allow_html=True)
        if st.button("↻ REFRESH", key="cve_refresh"):
            st.rerun()
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("TOTAL CVEs", f"{stats.get('total', 0):,}")
    with col2: st.metric("CRITICAL", f"{stats.get('critical', 0):,}")
    with col3: st.metric("AVG CVSS", f"{stats.get('avg_cvss_score', 0):.2f}")
    with col4: st.metric("HIGH", f"{stats.get('by_severity', {}).get('HIGH', 0):,}")

    st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>SEVERITY DISTRIBUTION</div>", unsafe_allow_html=True)
        by_sev = {k: v for k, v in stats.get("by_severity", {}).items() if v > 0}
        if by_sev:
            SEV_COLORS = {"CRITICAL": T["--red"], "HIGH": T["--orange"], "MEDIUM": T["--yellow"], "LOW": T["--green"]}
            fig = go.Figure(go.Pie(
                labels=list(by_sev.keys()), values=list(by_sev.values()),
                marker=dict(colors=[SEV_COLORS.get(s, T["--text-dim"]) for s in by_sev.keys()],
                            line=dict(color=T["--bg-primary"], width=2)),
                hole=0.6, textfont=dict(family="JetBrains Mono", size=11),
                hovertemplate="<b>%{label}</b><br>%{value} CVEs<extra></extra>",
            ))
            fig.add_annotation(text=f"<b>{sum(by_sev.values())}</b><br><span style='font-size:10px'>TOTAL</span>",
                x=0.5, y=0.5, font=dict(family="Rajdhani", size=22, color=T["--cyan"]), showarrow=False)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", color=T["--text-secondary"]),
                showlegend=True, legend=dict(font=dict(family="JetBrains Mono", size=10), bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=20, b=20, l=20, r=20), height=280)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>TOP CVEs BY RISK SCORE</div>", unsafe_allow_html=True)
        if cves:
            SEV_COLORS = {"CRITICAL": T["--red"], "HIGH": T["--orange"], "MEDIUM": T["--yellow"], "LOW": T["--green"]}
            top10 = cves[:10]
            fig = go.Figure(go.Bar(
                x=[c["risk_score"] for c in top10],
                y=[c["cve_id"] for c in top10],
                orientation="h",
                marker=dict(color=[SEV_COLORS.get(c.get("cvss_severity", ""), T["--text-dim"]) for c in top10]),
                hovertemplate="<b>%{y}</b><br>Risk: %{x:.2f}<extra></extra>",
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", size=9, color=T["--text-secondary"]),
                xaxis=dict(range=[0, 1], gridcolor=T["--border"]),
                yaxis=dict(gridcolor=T["--border"]),
                margin=dict(t=10, b=10, l=10, r=10), height=280)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>CVE FEED</div>", unsafe_allow_html=True)
    sev_filter = st.selectbox("FILTER BY SEVERITY", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"], key="sa_cve_filter")
    filtered_cves = [c for c in cves if sev_filter == "ALL" or c.get("cvss_severity") == sev_filter]

    SEV_COLORS = {"CRITICAL": T["--red"], "HIGH": T["--orange"], "MEDIUM": T["--yellow"], "LOW": T["--green"]}
    for cve in filtered_cves:
        sev = cve.get("cvss_severity", "UNKNOWN")
        color = SEV_COLORS.get(sev, T["--text-dim"])
        techniques = ", ".join(cve.get("mitre_techniques", [])) or "—"
        cwes = ", ".join(cve.get("cwe_ids", [])) or "—"
        with st.expander(f"{cve['cve_id']} · CVSS {cve.get('cvss_score', '—')} · {sev}"):
            st.markdown(f"""
            <div style='font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{T["--text-secondary"]};line-height:1.6;'>
            <div style='color:{color};font-weight:600;margin-bottom:0.5rem;'>{sev} · Risk: {cve.get('risk_score', 0):.2f}</div>
            <div style='margin-bottom:0.5rem;'>{cve.get('description', '')[:400]}</div>
            <div><span style='color:{T["--text-dim"]};'>CWE:</span> {cwes}</div>
            <div><span style='color:{T["--text-dim"]};'>MITRE:</span> <span style='color:{T["--cyan"]};'>{techniques}</span></div>
            </div>""", unsafe_allow_html=True)
def render_ioc(T: dict):
    import httpx
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>IOC THREAT FEED</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>LIVE INDICATORS OF COMPROMISE · ALIENVAULT OTX · MITRE ATT&CK MAPPED</div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([3,1])
    with col1:
        limit = st.slider("NUMBER OF PULSES", min_value=5, max_value=20, value=10, key="ioc_limit")
    with col2:
        st.markdown("<div style='margin-top:1.8rem;'></div>", unsafe_allow_html=True)
        refresh = st.button("REFRESH FEED", use_container_width=True)

    try:
        r = httpx.get(f"{BACKEND_URL}/ioc/pulses", params={"limit": limit}, timeout=20)
        r.raise_for_status()
        data = r.json()
        pulses = data.get("pulses", [])
    except Exception as e:
        st.error(f"Backend error: {e}")
        return

    st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:1rem;'>{len(pulses)} THREAT PULSES · SOURCE: ALIENVAULT OTX</div>", unsafe_allow_html=True)

    TLP_COLORS = {"white": T["--text-dim"], "green": T["--green"], "amber": T["--yellow"], "red": T["--red"]}
    TYPE_COLORS = {"IPv4": T["--red"], "IPv6": T["--red"], "domain": T["--orange"], "hostname": T["--orange"], "URL": T["--yellow"], "FileHash-MD5": T["--cyan"], "FileHash-SHA1": T["--cyan"], "FileHash-SHA256": T["--cyan"], "email": T["--green"], "CVE": T["--orange"]}

    for pulse in pulses:
        tlp = pulse.get("tlp", "white").lower()
        tlp_color = TLP_COLORS.get(tlp, T["--text-dim"])
        tags = pulse.get("tags", [])
        tags_html = " ".join([f"<span style='background:{T['--tag-bg']};border-radius:3px;padding:0.1rem 0.4rem;font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T['--text-dim']};'>{t}</span>" for t in tags])

        with st.expander(f"{pulse.get('name', 'Unknown Pulse')}"):
            st.markdown(f"""
            <div style='display:flex;gap:0.6rem;margin-bottom:0.8rem;flex-wrap:wrap;align-items:center;'>
            <span style='background:{tlp_color}22;border:1px solid {tlp_color}55;border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{tlp_color};'>TLP: {tlp.upper()}</span>
            <span style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};'>{pulse.get("created","")[:10]}</span>
            <span style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};'>by {pulse.get("author","")}</span>
            </div>
            <div style='font-family:Inter,sans-serif;font-size:0.85rem;color:{T["--text-secondary"]};line-height:1.6;margin-bottom:0.8rem;'>{pulse.get("description","")}</div>
            <div style='display:flex;gap:0.3rem;flex-wrap:wrap;margin-bottom:1rem;'>{tags_html}</div>
            """, unsafe_allow_html=True)

            indicators = pulse.get("indicators", [])
            if indicators:
                st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:0.5rem;'>INDICATORS OF COMPROMISE</div>", unsafe_allow_html=True)
                for ioc in indicators:
                    ioc_type = ioc.get("type", "unknown")
                    ioc_color = TYPE_COLORS.get(ioc_type, T["--text-dim"])
                    mitre = ioc.get("mitre_technique", "")
                    st.markdown(f"""
                    <div style='background:{T["--input-bg"]};border:1px solid {T["--border"]};border-left:2px solid {ioc_color};border-radius:4px;padding:0.4rem 0.8rem;margin-bottom:0.3rem;display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                    <span style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{ioc_color};margin-right:0.5rem;'>{ioc_type}</span>
                    <span style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--text-primary"]};'>{ioc.get("indicator","")[:60]}</span>
                    </div>
                    <span style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--cyan"]};'>{mitre}</span>
                    </div>""", unsafe_allow_html=True)
def render_kill_chain(T: dict):
    import httpx
    import json
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>KILL CHAIN TIMELINE</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>MITRE ATT&CK · AI-GENERATED ATTACK PROGRESSION · PHASE-BY-PHASE ANALYSIS</div>
    </div>""", unsafe_allow_html=True)

    query = st.text_area("THREAT QUERY", placeholder="e.g. ransomware lateral movement techniques", height=90, key="killchain_query")
    generate = st.button("GENERATE KILL CHAIN", type="primary")

    if generate and query.strip():
        with st.spinner("Generating kill chain timeline..."):
            try:
                r = httpx.post(
                    f"{BACKEND_URL}/intel/killchain",
                    json={"query": query.strip()},
                    headers={"X-API-Key": API_KEY},
                    timeout=60,
                )
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                st.error(f"Backend error: {e}")
                return

        st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-top:3px solid {T["--cyan"]};border-radius:6px;padding:0.8rem 1rem;text-align:center;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-bottom:0.3rem;'>THREAT ID</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:1.2rem;font-weight:700;color:{T["--cyan"]};'>{data.get("threat_id", "—")}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-top:3px solid {T["--green"]};border-radius:6px;padding:0.8rem 1rem;text-align:center;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-bottom:0.3rem;'>THREAT NAME</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;color:{T["--green"]};'>{data.get("threat_name", "—")[:40]}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.5rem;'>ATTACK PROGRESSION</div>", unsafe_allow_html=True)

        SEV_COLORS = {"critical": T["--red"], "high": T["--orange"], "medium": T["--yellow"], "low": T["--green"]}
        phases = data.get("kill_chain", [])

        for i, phase in enumerate(phases):
            sev = phase.get("severity", "medium").lower()
            color = SEV_COLORS.get(sev, T["--text-dim"])
            is_last = i == len(phases) - 1
            st.markdown(f"""
            <div style='display:flex;align-items:flex-start;margin-bottom:0;'>
                <div style='display:flex;flex-direction:column;align-items:center;margin-right:1rem;'>
                    <div style='width:36px;height:36px;border-radius:50%;background:{color}22;border:2px solid {color};display:flex;align-items:center;justify-content:center;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{color};font-weight:700;flex-shrink:0;'>{i+1}</div>
                    {f'<div style="width:2px;height:40px;background:{color}44;margin:4px 0;"></div>' if not is_last else '<div style="height:4px;"></div>'}
                </div>
                <div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-left:3px solid {color};border-radius:8px;padding:1rem 1.2rem;margin-bottom:{"0.5rem" if not is_last else "0"};flex:1;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;'>
                        <div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:700;color:{T["--text-primary"]};'>{phase.get("phase", "")}</div>
                        <span style='background:{color}22;border:1px solid {color}55;border-radius:4px;padding:0.2rem 0.6rem;font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{color};text-transform:uppercase;'>{sev}</span>
                    </div>
                    <div style='display:flex;gap:0.5rem;margin-bottom:0.5rem;flex-wrap:wrap;'>
                        <span style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--cyan"]};'>{phase.get("technique_id", "")}</span>
                        <span style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};'>·</span>
                        <span style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-secondary"]};'>{phase.get("technique_name", "")}</span>
                        <span style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};'>·</span>
                        <span style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};'>{phase.get("tactic", "")}</span>
                    </div>
                    <div style='font-family:Inter,sans-serif;font-size:0.85rem;color:{T["--text-secondary"]};line-height:1.5;'>{phase.get("description", "")}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    elif generate:
        st.markdown(f"""<div style='background:{T["--warn-bg"]};border:1px solid {T["--warn-border"]};border-left:3px solid {T["--yellow"]};border-radius:6px;padding:0.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--yellow"]};'>QUERY REQUIRED</div>""", unsafe_allow_html=True)

def render_analytics(T: dict):
    import httpx
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>API ANALYTICS</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>REQUEST OBSERVABILITY · LATENCY TRACKING · ENDPOINT USAGE</div>
    </div>""", unsafe_allow_html=True)

    stats = None
    recent = []
    backend_online = False
    try:
        r = httpx.get(f"{BACKEND_URL}/analytics/requests", timeout=15)
        if r.status_code == 200:
            stats = r.json()
            backend_online = True
        r2 = httpx.get(f"{BACKEND_URL}/analytics/requests/recent", params={"limit": 20}, timeout=15)
        if r2.status_code == 200:
            recent = r2.json().get("requests", [])
    except Exception:
        pass

    if not backend_online:
        st.markdown(f"""
        <div style='background:{T["--warn-bg"]};border:1px solid {T["--warn-border"]};
        border-left:3px solid {T["--yellow"]};border-radius:8px;padding:1.2rem 1.5rem;'>
        <div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:700;
        color:{T["--yellow"]};margin-bottom:0.4rem;'>⏳ BACKEND WARMING UP</div>
        <div style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--text-secondary"]};line-height:1.6;'>
        Analytics requires the CyberMind backend. Click refresh after ~30 seconds.
        </div></div>""", unsafe_allow_html=True)
        if st.button("↻ REFRESH", key="analytics_refresh"):
            st.rerun()
        return

    col1, col2, col3, col4 = st.columns(4)
    by_status = stats.get("by_status_code", {})
    with col1: st.metric("TOTAL REQUESTS", f"{stats.get('total_requests', 0):,}")
    with col2: st.metric("AVG LATENCY", f"{stats.get('avg_latency_ms', 0):.1f}ms")
    with col3: st.metric("2xx SUCCESS", f"{by_status.get('200', 0) + by_status.get('201', 0):,}")
    with col4: st.metric("ERRORS", f"{by_status.get('500', 0) + by_status.get('404', 0):,}")

    st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>REQUESTS BY METHOD</div>", unsafe_allow_html=True)
        by_method = stats.get("by_method", {})
        if by_method:
            METHOD_COLORS = {"GET": T["--cyan"], "POST": T["--green"], "PATCH": T["--yellow"], "DELETE": T["--red"]}
            fig = go.Figure(go.Bar(
                x=list(by_method.keys()), y=list(by_method.values()),
                marker=dict(color=[METHOD_COLORS.get(m, T["--text-dim"]) for m in by_method.keys()]),
                hovertemplate="<b>%{x}</b><br>%{y} requests<extra></extra>",
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", size=10, color=T["--text-secondary"]),
                xaxis=dict(gridcolor=T["--border"]), yaxis=dict(gridcolor=T["--border"]),
                margin=dict(t=10, b=10, l=10, r=10), height=250)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>TOP ENDPOINTS</div>", unsafe_allow_html=True)
        top = stats.get("top_endpoints", [])
        if top:
            paths = [e["path"].replace("/api/v1/", "") for e in top]
            fig = go.Figure(go.Bar(
                x=[e["count"] for e in top], y=paths, orientation="h",
                marker=dict(color=T["--cyan"]),
                hovertemplate="<b>%{y}</b><br>%{x} requests<extra></extra>",
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", size=10, color=T["--text-secondary"]),
                xaxis=dict(gridcolor=T["--border"]), yaxis=dict(gridcolor=T["--border"]),
                margin=dict(t=10, b=10, l=10, r=10), height=250)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>RECENT REQUEST LOG</div>", unsafe_allow_html=True)

    STATUS_COLORS = {2: T["--green"], 3: T["--yellow"], 4: T["--orange"], 5: T["--red"]}
    for req in recent:
        code = req.get("status_code", 0)
        color = STATUS_COLORS.get(code // 100, T["--text-dim"])
        st.markdown(f"""
        <div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-radius:4px;
        padding:0.4rem 0.8rem;margin-bottom:0.3rem;display:flex;justify-content:space-between;'>
        <div style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--text-secondary"]};'>
        <span style='color:{T["--cyan"]};margin-right:0.5rem;'>{req.get("method")}</span>{req.get("path")}</div>
        <div style='display:flex;gap:1rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;'>
        <span style='color:{color};'>{code}</span>
        <span style='color:{T["--text-dim"]};'>{req.get("latency_ms", 0):.1f}ms</span></div></div>""",
        unsafe_allow_html=True)


def main():
    theme = st.session_state.theme
    T = DARK if theme == "dark" else LIGHT
    is_dark = theme == "dark"

    st.markdown(get_css(T), unsafe_allow_html=True)

    _, toggle_col = st.columns([9, 1])
    with toggle_col:
        if st.button("☀ LIGHT" if is_dark else "◑ DARK", key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()

    st.sidebar.markdown(f"""<div style='margin-bottom:1.5rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:1.6rem;font-weight:700;color:{T["--cyan"]};letter-spacing:0.15em;text-transform:uppercase;'>⬡ CYBERMIND</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};letter-spacing:0.2em;text-transform:uppercase;margin-top:0.2rem;'>AI THREAT INTELLIGENCE</div>
    </div>""", unsafe_allow_html=True)

    st.sidebar.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.5rem;'>NAVIGATION</div>", unsafe_allow_html=True)

    TABS = {"Overview": " ", "Threat Intel": " ", "Sigma Rules": " ", "CVE Intel": " ", "Alerts": " ", "Playbooks": " ", "Entity Graph": " ", "IOC": " ", "Kill Chain": " ", "Analytics": " "}
    selected = st.sidebar.radio("nav", list(TABS.keys()), format_func=lambda x: f"{TABS[x]}  {x}", label_visibility="collapsed")

    st.sidebar.markdown(f"""<hr style='border-color:{T["--border"]};margin:1.5rem 0;'>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};'>
    <div>v1.0.0 · MITRE ATT&CK</div><div style='margin-top:0.3rem;'>LLaMA 3.3 · FAISS · RAG</div>
    <div style='margin-top:0.8rem;color:{T["--green"]};'>● OPERATIONAL</div></div>""", unsafe_allow_html=True)

    _, rag_svc, llm_svc = load_services()

    if selected == "Overview":
        render_overview(T, rag_svc, llm_svc)
    elif selected == "Threat Intel":
        render_threat_intel(T, rag_svc, llm_svc)
        
    elif selected == "Alerts":
        render_alerts(T, llm_svc)
    elif selected == "Playbooks":
        render_playbooks(T, rag_svc, llm_svc)
    elif selected == "Entity Graph":
        render_entity_graph(T, llm_svc)
    elif selected == "Sigma Rules":
        render_sigma(T)
    elif selected == "CVE Intel":
        render_cve_intel(T)
    elif selected == "IOC":
        render_ioc(T)
    elif selected == "Kill Chain":
        render_kill_chain(T)
    elif selected == "Analytics":
        render_analytics(T)


if __name__ == "__main__":
    main()






