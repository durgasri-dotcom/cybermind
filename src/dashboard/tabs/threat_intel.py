import httpx
import streamlit as st

from configs.settings import settings

BACKEND = f"http://127.0.0.1:{settings.api_port}{settings.api_prefix}"


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


def render(T: dict):
    st.markdown(f"""
    <div style='margin-bottom: 2rem;'>
        <div style='font-family: Rajdhani, sans-serif; font-size: 2rem; font-weight: 700;
                    color: {T["--text-primary"]}; letter-spacing: 0.05em;'>
            THREAT INTELLIGENCE Q&A
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em; margin-top: 0.3rem;'>
            RAG-POWERED ANALYSIS · MITRE ATT&CK · LLAMA 3.3 70B
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                    color: {T["--text-dim"]}; letter-spacing: 0.15em;
                    text-transform: uppercase; margin-bottom: 0.8rem;'>ANALYST QUERY</div>
        <div style='display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;'>
            <span style='background: {T["--cyan-dim"]}; border: 1px solid {T["--cyan"]}44;
                         border-radius: 4px; padding: 0.3rem 0.7rem;
                         font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                         color: {T["--cyan"]}; letter-spacing: 0.05em;'>
                How does APT29 achieve persistence?
            </span>
            <span style='background: {T["--cyan-dim"]}; border: 1px solid {T["--cyan"]}44;
                         border-radius: 4px; padding: 0.3rem 0.7rem;
                         font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                         color: {T["--cyan"]}; letter-spacing: 0.05em;'>
                Explain T1059.001 PowerShell techniques
            </span>
            <span style='background: {T["--cyan-dim"]}; border: 1px solid {T["--cyan"]}44;
                         border-radius: 4px; padding: 0.3rem 0.7rem;
                         font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                         color: {T["--cyan"]}; letter-spacing: 0.05em;'>
                Common ransomware lateral movement TTPs
            </span>
            <span style='background: {T["--cyan-dim"]}; border: 1px solid {T["--cyan"]}44;
                         border-radius: 4px; padding: 0.3rem 0.7rem;
                         font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                         color: {T["--cyan"]}; letter-spacing: 0.05em;'>
                Detect credential dumping with Splunk
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    query = st.text_area(
        "ANALYST QUERY",
        placeholder="e.g. How does APT29 achieve persistence on Windows?",
        height=90,
        key="intel_query",
    )

    col1, col2 = st.columns([4, 1])
    with col1:
        top_k = st.slider(
            "CONTEXT CHUNKS TO RETRIEVE",
            min_value=1, max_value=15, value=5,
            key="intel_topk",
        )
    with col2:
        analyze = st.button("⟶ ANALYZE", type="primary", use_container_width=True)

    if analyze and query.strip():
        with st.spinner("Retrieving vectors and generating analysis..."):
            result = query_intel(query.strip(), top_k)

        if "error" in result:
            st.markdown(f"""
            <div style='background: {T["--error-bg"]}; border: 1px solid {T["--error-border"]};
                        border-left: 3px solid {T["--red"]}; border-radius: 6px;
                        padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                        font-size: 0.8rem; color: {T["--red"]};'>
                ⚠ {result["error"]}
            </div>
            """, unsafe_allow_html=True)
            return

        latency = result.get("latency_ms", 0)
        chunks = result.get("num_chunks_retrieved", 0)
        rag_ready = result.get("rag_ready", False)

        c1, c2, c3 = st.columns(3)
        for col, label, value, color in [
            (c1, "LATENCY", f"{latency:.0f}ms",
             T["--green"] if latency < 3000 else T["--yellow"]),
            (c2, "CHUNKS RETRIEVED", str(chunks), T["--cyan"]),
            (c3, "RAG STATUS",
             "READY" if rag_ready else "OFFLINE",
             T["--green"] if rag_ready else T["--red"]),
        ]:
            with col:
                st.markdown(f"""
                <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                            border-top: 3px solid {color}; border-radius: 6px;
                            padding: 0.8rem 1rem; text-align: center;'>
                    <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                                color: {T["--text-dim"]}; letter-spacing: 0.15em;
                                text-transform: uppercase; margin-bottom: 0.3rem;'>{label}</div>
                    <div style='font-family: Rajdhani, sans-serif; font-size: 1.4rem;
                                font-weight: 700; color: {color};'>{value}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                    unsafe_allow_html=True)

        st.markdown(f"""
        <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                    color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                    text-transform: uppercase; margin-bottom: 1rem;'>
            INTELLIGENCE REPORT
        </div>
        """, unsafe_allow_html=True)

        analysis = result.get("analysis", "")
        st.markdown(f"""
        <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                    border-left: 3px solid {T["--cyan"]}; border-radius: 8px;
                    padding: 1.5rem; line-height: 1.8;
                    font-family: Inter, sans-serif; font-size: 0.9rem;
                    color: {T["--text-primary"]}; white-space: pre-wrap;'>
            {analysis}
        </div>
        """, unsafe_allow_html=True)

        similar = result.get("similar_threats", [])
        if similar:
            st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                        unsafe_allow_html=True)
            st.markdown(f"""
            <div style='font-family: Rajdhani, sans-serif; font-size: 1.1rem; font-weight: 600;
                        color: {T["--text-secondary"]}; letter-spacing: 0.1em;
                        text-transform: uppercase; margin-bottom: 1rem;'>
                SIMILAR THREATS RETRIEVED
            </div>
            """, unsafe_allow_html=True)

            for t in similar:
                score = t["score"]
                score_color = (T["--green"] if score > 0.6
                               else T["--yellow"] if score > 0.4
                               else T["--text-dim"])
                st.markdown(f"""
                <div style='background: {T["--bg-card"]}; border: 1px solid {T["--border"]};
                            border-radius: 6px; padding: 0.8rem 1rem; margin-bottom: 0.4rem;
                            display: flex; justify-content: space-between; align-items: flex-start;'>
                    <div>
                        <span style='font-family: JetBrains Mono, monospace; font-size: 0.75rem;
                                     color: {T["--cyan"]};'>{t["threat_id"]}</span>
                        <span style='font-family: Rajdhani, sans-serif; font-size: 0.95rem;
                                     color: {T["--text-primary"]}; margin-left: 0.8rem;
                                     font-weight: 600;'>{t["name"]}</span>
                        <div style='font-family: Inter, sans-serif; font-size: 0.75rem;
                                    color: {T["--text-dim"]}; margin-top: 0.3rem;'>
                            {t.get("chunk_preview", "")}
                        </div>
                    </div>
                    <div style='font-family: JetBrains Mono, monospace; font-size: 0.75rem;
                                color: {score_color}; white-space: nowrap; margin-left: 1rem;'>
                        {score:.4f}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        chunks_data = result.get("retrieved_chunks", [])
        if chunks_data:
            st.markdown(f"<div style='margin: 1.5rem 0; border-top: 1px solid {T['--border']};'></div>",
                        unsafe_allow_html=True)
            with st.expander("◈ VIEW RAW CONTEXT CHUNKS"):
                for i, chunk in enumerate(chunks_data, 1):
                    st.markdown(f"""
                    <div style='background: {T["--input-bg"]}; border: 1px solid {T["--border"]};
                                border-radius: 4px; padding: 0.8rem; margin-bottom: 0.5rem;'>
                        <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                                    color: {T["--cyan"]}; letter-spacing: 0.1em;
                                    margin-bottom: 0.4rem;'>CHUNK {i:02d}</div>
                        <div style='font-family: Inter, sans-serif; font-size: 0.8rem;
                                    color: {T["--text-secondary"]}; line-height: 1.6;'>
                            {chunk}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    elif analyze:
        st.markdown(f"""
        <div style='background: {T["--warn-bg"]}; border: 1px solid {T["--warn-border"]};
                    border-left: 3px solid {T["--yellow"]}; border-radius: 6px;
                    padding: 0.8rem 1rem; font-family: JetBrains Mono, monospace;
                    font-size: 0.75rem; color: {T["--yellow"]};'>
            ⚠ QUERY REQUIRED — Enter a threat intelligence question
        </div>
        """, unsafe_allow_html=True)