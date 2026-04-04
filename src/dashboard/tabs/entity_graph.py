import math

import httpx
import plotly.graph_objects as go
import streamlit as st


import os
BACKEND = os.getenv("CYBERMIND_BACKEND_URL", "https://cybermind-0y0t.onrender.com/api/v1")

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


def fetch_entities(entity_type=None):
    try:
        params = {"limit": 100}
        if entity_type:
            params["entity_type"] = entity_type
        r = httpx.get(f"{BACKEND}/entities", params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def enrich_entity(entity_id: str):
    try:
        r = httpx.post(
            f"{BACKEND}/entities/enrich",
            json={"entity_id": entity_id},
            timeout=60,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def create_entity(payload: dict):
    try:
        r = httpx.post(f"{BACKEND}/entities", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def build_graph(entities: list, T: dict) -> go.Figure:
    node_x, node_y = [], []
    node_text, node_hover = [], []
    node_colors, node_sizes = [], []
    edge_x, edge_y = [], []
    edge_labels = []

    n = len(entities)
    pos = {}
    for i, entity in enumerate(entities):
        angle = 2 * math.pi * i / max(n, 1)
        radius = 0.7 + (0.15 * (i % 3))
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        pos[entity["entity_id"]] = (x, y)
        node_x.append(x)
        node_y.append(y)
        node_text.append(entity["name"])
        node_hover.append(
            f"<b>{entity['name']}</b><br>"
            f"{entity.get('entity_type', '').upper()}<br>"
            f"ID: {entity['entity_id']}<br>"
            f"Techniques: {len(entity.get('associated_techniques', []))}"
        )
        color_key = ENTITY_TYPE_COLORS.get(entity.get("entity_type", ""), "--text-secondary")
        node_colors.append(T[color_key])
        node_sizes.append(18 + len(entity.get("associated_techniques", [])) * 0.8)

    # ── explicit relationships ─────────────────────────────────────────────────
    for entity in entities:
        x, y = pos[entity["entity_id"]]
        for rel in entity.get("relationships", []):
            target_id = rel.get("target_entity_id")
            if target_id in pos:
                tx, ty = pos[target_id]
                edge_x += [x, tx, None]
                edge_y += [y, ty, None]

    # ── implicit edges from shared MITRE techniques ───────────────────────────
    for i, e1 in enumerate(entities):
        t1 = set(e1.get("associated_techniques", []))
        if not t1:
            continue
        for j, e2 in enumerate(entities):
            if j <= i:
                continue
            t2 = set(e2.get("associated_techniques", []))
            shared = t1 & t2
            if shared:
                x1, y1 = pos[e1["entity_id"]]
                x2, y2 = pos[e2["entity_id"]]
                edge_x += [x1, x2, None]
                edge_y += [y1, y2, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=1, color=T["--border"]),
        hoverinfo="none",
        opacity=0.6,
    )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        textfont=dict(family="Rajdhani", size=11, color=T["--text-secondary"]),
        hovertext=node_hover,
        hoverinfo="text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color=T["--bg-primary"]),
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=T["--plot-bg"],
            showlegend=False,
            height=500,
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=[
                dict(
                    text="Node size = technique count · Lines = shared techniques or explicit relationships",
                    xref="paper", yref="paper",
                    x=0.5, y=-0.02,
                    showarrow=False,
                    font=dict(family="JetBrains Mono", size=9, color=T["--text-dim"]),
                )
            ],
        ),
    )
    return fig

def render(T: dict):
    st.markdown(f"""
    <div style='margin-bottom: 2rem;'>
        <div style='font-family: Rajdhani, sans-serif; font-size: 2rem; font-weight: 700;
                    color: {T["--text-primary"]}; letter-spacing: 0.05em;'>ENTITY GRAPH</div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em; margin-top: 0.3rem;'>
            THREAT ACTORS · MALWARE · TOOLS · RELATIONSHIP MAPPING
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_graph, tab_list, tab_add = st.tabs(
        ["RELATIONSHIP GRAPH", "ENTITY LIST", "ADD ENTITY"]
    )

    with tab_graph:
        filter_col, _ = st.columns([2, 5])
        with filter_col:
            entity_type_filter = st.selectbox(
                "FILTER BY TYPE",
                ["All", "threat_actor", "malware", "tool",
                 "campaign", "infrastructure"],
                key="graph_filter",
            )

        data = fetch_entities(
            None if entity_type_filter == "All" else entity_type_filter
        )

        if "error" in data:
            st.markdown(f"""
            <div style='background: {T["--error-bg"]}; border: 1px solid {T["--error-border"]};
                        border-left: 3px solid {T["--red"]}; border-radius: 6px;
                        padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                        font-size: 0.8rem; color: {T["--red"]};'>⚠ {data["error"]}</div>
            """, unsafe_allow_html=True)
            return

        entities = data.get("entities", [])

        if not entities:
            st.markdown(f"""
            <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                        border-radius: 8px; padding: 3rem; text-align: center;
                        font-family: JetBrains Mono, monospace; font-size: 0.8rem;
                        color: {T["--text-dim"]};'>
                NO ENTITIES — Add entities from the Add Entity tab
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                        color: {T["--text-dim"]}; letter-spacing: 0.1em;
                        margin-bottom: 0.8rem;'>
                {len(entities)} ENTITIES · NODE SIZE = TECHNIQUE COUNT
            </div>
            """, unsafe_allow_html=True)

            legend_cols = st.columns(5)
            for col, (etype, color_key) in zip(
                legend_cols, ENTITY_TYPE_COLORS.items()
            ):
                with col:
                    st.markdown(f"""
                    <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                                color: {T[color_key]}; letter-spacing: 0.05em;'>
                        ● {etype.replace("_", " ").upper()}
                    </div>
                    """, unsafe_allow_html=True)

            st.plotly_chart(build_graph(entities, T), use_container_width=True)

    with tab_list:
        data = fetch_entities()
        entities = data.get("entities", []) if "error" not in data else []

        if not entities:
            st.markdown(f"""
            <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                        border-radius: 8px; padding: 2rem; text-align: center;
                        font-family: JetBrains Mono, monospace; font-size: 0.8rem;
                        color: {T["--text-dim"]};'>NO ENTITIES YET</div>
            """, unsafe_allow_html=True)
        else:
            for entity in entities:
                color_key = ENTITY_TYPE_COLORS.get(
                    entity.get("entity_type", ""), "--text-secondary"
                )
                color = T[color_key]
                icon = ENTITY_ICONS.get(entity.get("entity_type", ""), "?")

                with st.expander(
                    f"{icon}  {entity['name']} — "
                    f"{entity.get('entity_type', '').upper()}"
                ):
                    st.markdown(f"""
                    <div style='display: flex; gap: 0.6rem; margin-bottom: 1rem;'>
                        <span style='background: {color}22; border: 1px solid {color}55;
                                     border-radius: 4px; padding: 0.2rem 0.6rem;
                                     font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                                     color: {color};'>{entity["entity_id"]}</span>
                    </div>
                    <div style='font-family: Inter, sans-serif; font-size: 0.88rem;
                                color: {T["--text-secondary"]}; margin-bottom: 1rem;
                                line-height: 1.6;'>
                        {entity.get("description", "")[:400]}
                    </div>
                    """, unsafe_allow_html=True)

                    techniques = entity.get("associated_techniques", [])
                    if techniques:
                        tags_html = " ".join([
                            f"<span style='background: {T['--cyan-dim']}; "
                            f"border: 1px solid {T['--cyan']}33; border-radius: 3px; "
                            f"padding: 0.1rem 0.4rem; font-family: JetBrains Mono, monospace; "
                            f"font-size: 0.6rem; color: {T['--cyan']};'>{t}</span>"
                            for t in techniques[:10]
                        ])
                        st.markdown(f"""
                        <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                                    color: {T["--text-dim"]}; letter-spacing: 0.1em;
                                    margin-bottom: 0.5rem;'>ASSOCIATED TECHNIQUES</div>
                        <div style='display: flex; gap: 0.3rem; flex-wrap: wrap;
                                    margin-bottom: 1rem;'>{tags_html}</div>
                        """, unsafe_allow_html=True)

                    if st.button("⟶ AI ENRICH",
                                 key=f"enrich_{entity['entity_id']}"):
                        with st.spinner("Generating threat profile..."):
                            result = enrich_entity(entity["entity_id"])
                        if "error" not in result:
                            st.markdown(f"""
                            <div style='background: {T["--bg-card"]};
                                        border: 1px solid {T["--cyan"]}44;
                                        border-left: 3px solid {T["--cyan"]};
                                        border-radius: 6px; padding: 1rem;
                                        margin-top: 0.5rem; font-family: Inter, sans-serif;
                                        font-size: 0.88rem; color: {T["--text-primary"]};
                                        line-height: 1.7;'>
                                {result.get("threat_profile", "")}
                            </div>
                            """, unsafe_allow_html=True)
                            detections = result.get("recommended_detections", [])
                            if detections:
                                st.markdown(f"""
                                <div style='font-family: JetBrains Mono, monospace;
                                            font-size: 0.65rem; color: {T["--text-dim"]};
                                            letter-spacing: 0.1em; margin: 1rem 0 0.5rem;'>
                                    RECOMMENDED DETECTIONS
                                </div>
                                """, unsafe_allow_html=True)
                                for d in detections:
                                    st.markdown(f"""
                                    <div style='background: {T["--input-bg"]};
                                                border: 1px solid {T["--border"]};
                                                border-left: 2px solid {T["--green"]};
                                                border-radius: 4px; padding: 0.4rem 0.8rem;
                                                margin-bottom: 0.3rem;
                                                font-family: Inter, sans-serif;
                                                font-size: 0.82rem;
                                                color: {T["--text-secondary"]};'>
                                        ● {d}
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.error(result["error"])

    with tab_add:
        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1.5rem;'>
            ADD THREAT ENTITY
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            entity_id = st.text_input("ENTITY ID", placeholder="G0007",
                                       key="ent_id")
        with col_b:
            name = st.text_input("NAME", placeholder="APT28", key="ent_name")

        entity_type = st.selectbox(
            "TYPE",
            ["threat_actor", "malware", "tool", "campaign", "infrastructure"],
            key="ent_type",
        )
        description = st.text_area("DESCRIPTION", height=100, key="ent_desc")

        col_c, col_d = st.columns(2)
        with col_c:
            aliases = st.text_input("ALIASES (comma separated)",
                                     placeholder="Fancy Bear, Sofacy",
                                     key="ent_aliases")
            sectors = st.text_input("TARGETED SECTORS",
                                     placeholder="Government, Defense",
                                     key="ent_sectors")
        with col_d:
            techniques = st.text_input("ASSOCIATED TECHNIQUES",
                                        placeholder="T1059, T1078, T1566",
                                        key="ent_techniques")
            countries = st.text_input("TARGETED COUNTRIES",
                                       placeholder="US, UK, Ukraine",
                                       key="ent_countries")

        if st.button("⟶ ADD ENTITY", type="primary"):
            if not all([entity_id, name, description]):
                st.markdown(f"""
                <div style='background: {T["--warn-bg"]};
                            border: 1px solid {T["--warn-border"]};
                            border-left: 3px solid {T["--yellow"]}; border-radius: 6px;
                            padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                            font-size: 0.75rem; color: {T["--yellow"]};'>
                    ⚠ ENTITY ID, NAME, AND DESCRIPTION REQUIRED
                </div>
                """, unsafe_allow_html=True)
            else:
                payload = {
                    "entity_id": entity_id.strip(),
                    "name": name.strip(),
                    "entity_type": entity_type,
                    "description": description.strip(),
                    "aliases": [a.strip() for a in aliases.split(",") if a.strip()],
                    "associated_techniques": [
                        t.strip() for t in techniques.split(",") if t.strip()
                    ],
                    "targeted_sectors": [
                        s.strip() for s in sectors.split(",") if s.strip()
                    ],
                    "targeted_countries": [
                        c.strip() for c in countries.split(",") if c.strip()
                    ],
                    "source": "MITRE ATT&CK",
                }
                result = create_entity(payload)
                if "error" not in result:
                    st.markdown(f"""
                    <div style='background: {T["--success-bg"]};
                                border: 1px solid {T["--success-border"]};
                                border-left: 3px solid {T["--green"]}; border-radius: 6px;
                                padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                                font-size: 0.75rem; color: {T["--green"]};'>
                        ✓ ENTITY '{name.upper()}' ADDED SUCCESSFULLY
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error(result["error"])
