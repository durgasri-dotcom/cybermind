import streamlit as st
import httpx
from configs.settings import settings

BACKEND = f"http://localhost:{settings.api_port}{settings.api_prefix}"


def query_intel(query: str, top_k: int = 5):
    try:
        r = httpx.post(
            f"{BACKEND}/intel/query",
            json={"query": query, "top_k": top_k},
            timeout=60,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def find_similar(query: str, top_k: int = 10):
    try:
        r = httpx.post(
            f"{BACKEND}/intel/similar",
            params={"query": query, "top_k": top_k},
            timeout=30,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def render():
    st.title("🔍 Threat Intelligence Q&A")
    st.caption("Ask anything about MITRE ATT&CK techniques, threat actors, or CVEs.")

    with st.form("intel_form"):
        query = st.text_area(
            "Your Question",
            placeholder="e.g. How does APT29 achieve persistence on Windows? What are common lateral movement techniques?",
            height=100,
        )
        col1, col2 = st.columns([3, 1])
        with col1:
            top_k = st.slider("Context chunks to retrieve", min_value=1, max_value=15, value=5)
        with col2:
            submitted = st.form_submit_button("Analyze", use_container_width=True)

    if submitted and query.strip():
        with st.spinner("Retrieving threat intelligence..."):
            result = query_intel(query.strip(), top_k)

        if "error" in result:
            st.error(f"Backend error: {result['error']}")
            return

        st.divider()

        col_meta1, col_meta2, col_meta3 = st.columns(3)
        col_meta1.metric("Latency", f"{result.get('latency_ms', 0):.0f}ms")
        col_meta2.metric("Chunks Retrieved", result.get("num_chunks_retrieved", 0))
        col_meta3.metric("RAG Ready", "✅" if result.get("rag_ready") else "⚠️")

        st.divider()
        st.subheader("Analysis")
        st.markdown(result.get("analysis", "No analysis returned."))

        similar = result.get("similar_threats", [])
        if similar:
            st.divider()
            st.subheader("Similar Threats Found")
            for t in similar:
                with st.expander(f"{t['threat_id']} — {t['name']} (score: {t['score']})"):
                    st.caption(t.get("chunk_preview", ""))

        chunks = result.get("retrieved_chunks", [])
        if chunks:
            st.divider()
            with st.expander("Retrieved Context Chunks"):
                for i, chunk in enumerate(chunks, 1):
                    st.markdown(f"**Chunk {i}**")
                    st.text(chunk)
                    st.divider()

    elif submitted:
        st.warning("Please enter a question.")