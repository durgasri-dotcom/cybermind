import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import datetime
import math
import time

import plotly.graph_objects as go
import streamlit as st

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


@st.cache_resource(show_spinner="Loading CyberMind AI engine...")
def load_services():
    from configs.logging_config import configure_logging
    configure_logging()
    from src.backend.services.embedding_service import get_embedding_service
    from src.backend.services.llm_service import get_llm_service
    from src.backend.services.rag_service import get_rag_service
    embedding_svc = get_embedding_service()
    rag_svc = get_rag_service()
    rag_svc.load_index()
    llm_svc = get_llm_service()
    return embedding_svc, rag_svc, llm_svc


# ── Helpers ────────────────────────────────────────────────────────────────────

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


# ── Tab renderers ──────────────────────────────────────────────────────────────

def render_overview(T: dict, rag_svc, llm_svc):
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>THREAT INTELLIGENCE OVERVIEW</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>REAL-TIME PLATFORM STATUS · MITRE ATT&CK · NVD CVE</div>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(status_card("PLATFORM STATUS", "OPERATIONAL", T["--green"], T), unsafe_allow_html=True)
    with col2: st.markdown(status_card("VECTOR STORE", "READY" if rag_svc.is_ready else "LOADING", T["--green"] if rag_svc.is_ready else T["--yellow"], T), unsafe_allow_html=True)
    with col3: st.markdown(status_card("THREATS INDEXED", f"{rag_svc.num_vectors:,}", T["--cyan"], T), unsafe_allow_html=True)
    with col4: st.markdown(status_card("LLM ENGINE", "LLAMA 3.3", T["--cyan"], T), unsafe_allow_html=True)

    st.markdown(f"<div style='margin:2rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>THREAT DISTRIBUTION BY SEVERITY</div>", unsafe_allow_html=True)
        SEV_COLORS = {"critical": T["--red"], "high": T["--orange"], "medium": T["--yellow"], "low": T["--green"], "unknown": T["--text-dim"]}
        by_sev = {s: 0 for s in SEV_COLORS}
        for a in st.session_state.alerts:
            pass
        filtered = {k: v for k, v in by_sev.items() if v > 0}
        if not filtered:
            from configs.settings import settings as cfg
            import json
            from pathlib import Path
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
                hole=0.6,
                textfont=dict(family="JetBrains Mono", size=11, color=T["--text-primary"]),
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
            ("RAG", rag_svc.is_ready, f"vectors: {rag_svc.num_vectors}"),
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
             ("VECTOR BACKEND", "FAISS" if not cfg.use_pinecone else "Pinecone"), ("RAG CHUNKS", f"{rag_svc.num_vectors:,}")]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-radius:8px;padding:1rem 1.2rem;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.4rem;'>{label}</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:600;color:{T["--text-secondary"]};'>{value}</div></div>""", unsafe_allow_html=True)


def render_threat_intel(T: dict, rag_svc, llm_svc):
    st.markdown(f"""
    <div style='margin-bottom:2rem;'>
    <div style='font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:{T["--text-primary"]};letter-spacing:0.05em;'>THREAT INTELLIGENCE Q&A</div>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{T["--text-dim"]};letter-spacing:0.15em;margin-top:0.3rem;'>RAG-POWERED ANALYSIS · MITRE ATT&CK · LLAMA 3.3 70B</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-radius:8px;padding:1.5rem;margin-bottom:1.5rem;'>
    <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T["--text-dim"]};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.8rem;'>ANALYST QUERY</div>
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
        with st.spinner("Retrieving vectors and generating analysis..."):
            start = time.perf_counter()
            retrieval_results = rag_svc.retrieve(query=query.strip(), top_k=top_k)
            chunks = [r["chunk"] for r in retrieval_results]
            metadata = [r["metadata"] for r in retrieval_results]
            threat_id = metadata[0].get("threat_id", "General") if metadata else "General"
            threat_name = metadata[0].get("name", query[:80]) if metadata else query[:80]
            analysis, _ = llm_svc.analyze_threat(
                threat_id=threat_id, threat_name=threat_name,
                threat_description=chunks[0] if chunks else query,
                rag_context=chunks, analyst_query=query,
            )
            elapsed = (time.perf_counter() - start) * 1000

        c1, c2, c3 = st.columns(3)
        for col, label, value, color in [
            (c1, "LATENCY", f"{elapsed:.0f}ms", T["--green"] if elapsed < 3000 else T["--yellow"]),
            (c2, "CHUNKS RETRIEVED", str(len(chunks)), T["--cyan"]),
            (c3, "RAG STATUS", "READY" if rag_svc.is_ready else "OFFLINE", T["--green"] if rag_svc.is_ready else T["--red"]),
        ]:
            with col:
                st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-top:3px solid {color};border-radius:6px;padding:0.8rem 1rem;text-align:center;'>
                <div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;color:{T["--text-dim"]};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.3rem;'>{label}</div>
                <div style='font-family:Rajdhani,sans-serif;font-size:1.4rem;font-weight:700;color:{color};'>{value}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>INTELLIGENCE REPORT</div>", unsafe_allow_html=True)
        st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-left:3px solid {T["--cyan"]};border-radius:8px;padding:1.5rem;line-height:1.8;font-family:Inter,sans-serif;font-size:0.9rem;color:{T["--text-primary"]};white-space:pre-wrap;'>{analysis}</div>""", unsafe_allow_html=True)

        if retrieval_results:
            st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;color:{T['--text-secondary']};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;'>SIMILAR THREATS RETRIEVED</div>", unsafe_allow_html=True)
            seen = set()
            for r in retrieval_results:
                tid = r["metadata"].get("threat_id", "unknown")
                if tid not in seen:
                    seen.add(tid)
                    score = r["score"]
                    sc = T["--green"] if score > 0.6 else T["--yellow"] if score > 0.4 else T["--text-dim"]
                    st.markdown(f"""<div style='background:{T["--bg-card"]};border:1px solid {T["--border"]};border-radius:6px;padding:0.8rem 1rem;margin-bottom:0.4rem;display:flex;justify-content:space-between;align-items:flex-start;'>
                    <div><span style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{T["--cyan"]};'>{tid}</span>
                    <span style='font-family:Rajdhani,sans-serif;font-size:0.95rem;color:{T["--text-primary"]};margin-left:0.8rem;font-weight:600;'>{r["metadata"].get("name", tid)}</span>
                    <div style='font-family:Inter,sans-serif;font-size:0.75rem;color:{T["--text-dim"]};margin-top:0.3rem;'>{r["chunk"][:150]}...</div></div>
                    <div style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{sc};white-space:nowrap;margin-left:1rem;'>{score:.4f}</div></div>""", unsafe_allow_html=True)

        if chunks:
            st.markdown(f"<div style='margin:1.5rem 0;border-top:1px solid {T['--border']};'></div>", unsafe_allow_html=True)
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
                rag_context = rag_svc.retrieve_chunks(query=f"incident response {threat_id} containment", top_k=3)
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
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{T['--text-dim']};letter-spacing:0.1em;margin-bottom:0.8rem;'>{len(entities)} ENTITIES · NODE SIZE = TECHNIQUE COUNT</div>", unsafe_allow_html=True)
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
                node_x.append(x); node_y.append(y)
                node_text.append(entity["name"])
                node_hover.append(f"<b>{entity['name']}</b><br>{entity.get('entity_type','').upper()}<br>ID: {entity['entity_id']}")
                color_key = ENTITY_TYPE_COLORS.get(entity.get("entity_type", ""), "--text-secondary")
                node_colors.append(T[color_key])
                node_sizes.append(18 + len(entity.get("associated_techniques", [])) * 0.8)

            fig = go.Figure(go.Scatter(x=node_x, y=node_y, mode="markers+text", text=node_text,
                textposition="top center", textfont=dict(family="Rajdhani", size=11, color=T["--text-secondary"]),
                hovertext=node_hover, hoverinfo="text",
                marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color=T["--bg-primary"]))))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=T["--plot-bg"],
                showlegend=False, height=450, margin=dict(t=20, b=20, l=20, r=20),
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


# ── Main ───────────────────────────────────────────────────────────────────────

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

    TABS = {"Overview": "🛡️", "Threat Intel": "🔍", "Alerts": "🚨", "Playbooks": "📋", "Entity Graph": "🕸️"}
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


if __name__ == "__main__":
    main()