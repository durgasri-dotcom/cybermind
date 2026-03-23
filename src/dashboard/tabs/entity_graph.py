import streamlit as st
import httpx
import plotly.graph_objects as go
from configs.settings import settings

BACKEND = f"http://localhost:{settings.api_port}{settings.api_prefix}"


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


ENTITY_COLORS = {
    "threat_actor": "#ff4b4b",
    "malware": "#ff8c00",
    "tool": "#ffd700",
    "campaign": "#00b4d8",
    "infrastructure": "#9e9e9e",
}


def build_relationship_graph(entities: list) -> go.Figure:
    node_x, node_y, node_text, node_colors = [], [], [], []
    edge_x, edge_y = [], []

    import math
    n = len(entities)
    for i, entity in enumerate(entities):
        angle = 2 * math.pi * i / max(n, 1)
        x = math.cos(angle)
        y = math.sin(angle)
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{entity['name']}<br>{entity['entity_type']}")
        node_colors.append(ENTITY_COLORS.get(entity.get("entity_type", ""), "#9e9e9e"))

        for rel in entity.get("relationships", []):
            target_id = rel.get("target_entity_id")
            target = next((e for e in entities if e["entity_id"] == target_id), None)
            if target:
                t_idx = entities.index(target)
                t_angle = 2 * math.pi * t_idx / max(n, 1)
                edge_x += [x, math.cos(t_angle), None]
                edge_y += [y, math.sin(t_angle), None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=1, color="#555"),
        hoverinfo="none",
    )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hoverinfo="text",
        marker=dict(size=14, color=node_colors, line=dict(width=1, color="#fff")),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    return fig


def render():
    st.title("🕸️ Entity Graph")
    st.caption("Threat actors, malware families, tools, and their relationships.")

    tab_graph, tab_list, tab_add = st.tabs(["Relationship Graph", "Entity List", "Add Entity"])

    with tab_graph:
        entity_type_filter = st.selectbox(
            "Filter by type",
            ["All", "threat_actor", "malware", "tool", "campaign", "infrastructure"],
        )

        data = fetch_entities(None if entity_type_filter == "All" else entity_type_filter)

        if "error" in data:
            st.error(f"Backend error: {data['error']}")
            return

        entities = data.get("entities", [])

        if not entities:
            st.info("No entities loaded yet. Add entities or run the MITRE ingestion pipeline.")
            return

        st.caption(f"{len(entities)} entities loaded")
        fig = build_relationship_graph(entities)
        st.plotly_chart(fig, use_container_width=True)

    with tab_list:
        data = fetch_entities()
        entities = data.get("entities", []) if "error" not in data else []

        for entity in entities:
            icon = {"threat_actor": "", "malware": "", "tool": "", "campaign": ""}.get(
                entity.get("entity_type"), "❓"
            )
            with st.expander(f"{icon} {entity['name']} — {entity.get('entity_type', 'unknown')}"):
                st.markdown(f"**ID:** `{entity['entity_id']}`")
                st.markdown(f"**Description:** {entity.get('description', '')[:300]}")

                techniques = entity.get("associated_techniques", [])
                if techniques:
                    st.markdown(f"**Techniques:** {', '.join(techniques[:10])}")

                if st.button("AI Enrich", key=f"enrich_{entity['entity_id']}"):
                    with st.spinner("Generating threat profile..."):
                        result = enrich_entity(entity["entity_id"])
                    if "error" not in result:
                        st.markdown("**Threat Profile:**")
                        st.markdown(result.get("threat_profile", ""))
                        detections = result.get("recommended_detections", [])
                        if detections:
                            st.markdown("**Recommended Detections:**")
                            for d in detections:
                                st.markdown(f"- {d}")
                    else:
                        st.error(result["error"])

    with tab_add:
        st.subheader("Add Entity")

        with st.form("add_entity_form"):
            entity_id = st.text_input("Entity ID", placeholder="G0007")
            name = st.text_input("Name", placeholder="APT28")
            entity_type = st.selectbox("Type", ["threat_actor", "malware", "tool", "campaign", "infrastructure"])
            description = st.text_area("Description", height=100)
            aliases = st.text_input("Aliases (comma separated)", placeholder="Fancy Bear, Sofacy")
            techniques = st.text_input("Associated Techniques (comma separated)", placeholder="T1059, T1078")
            sectors = st.text_input("Targeted Sectors (comma separated)", placeholder="Government, Defense")
            countries = st.text_input("Targeted Countries (comma separated)", placeholder="US, UK, Ukraine")
            submitted = st.form_submit_button("Add Entity")

        if submitted:
            if not all([entity_id, name, description]):
                st.warning("Entity ID, name, and description are required.")
            else:
                payload = {
                    "entity_id": entity_id.strip(),
                    "name": name.strip(),
                    "entity_type": entity_type,
                    "description": description.strip(),
                    "aliases": [a.strip() for a in aliases.split(",") if a.strip()],
                    "associated_techniques": [t.strip() for t in techniques.split(",") if t.strip()],
                    "targeted_sectors": [s.strip() for s in sectors.split(",") if s.strip()],
                    "targeted_countries": [c.strip() for c in countries.split(",") if c.strip()],
                }
                result = create_entity(payload)
                if "error" not in result:
                    st.success(f"Entity '{name}' added successfully.")
                else:
                    st.error(result["error"])