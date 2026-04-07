from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from configs.logging_config import get_logger
from configs.settings import settings
from src.backend.services.llm_service import LLMService, get_llm_service
from src.backend.services.rag_service import RAGService, get_rag_service

logger = get_logger(__name__)
router = APIRouter()


class IntelQueryRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=2000)
    threat_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class SimilarThreat(BaseModel):
    threat_id: str
    name: str
    score: float
    chunk_preview: str


class IntelQueryResponse(BaseModel):
    sources: list[str] = []
    query: str
    analysis: str
    retrieved_chunks: list[str]
    similar_threats: list[SimilarThreat]
    model_used: str
    num_chunks_retrieved: int
    latency_ms: float
    rag_ready: bool


@router.post("/intel/query")
async def query_threat_intel(
    body: IntelQueryRequest,
    rag_svc: RAGService = Depends(get_rag_service),
    llm_svc: LLMService = Depends(get_llm_service),
):
    total_start = time.perf_counter()

    # ── hybrid retrieval: MITRE + CVEs ────────────────────────────────────
    hybrid = rag_svc.retrieve_with_cves(query=body.query, top_k=body.top_k, max_cves=3)
    mitre_results = hybrid["mitre_results"]
    chunks = hybrid["all_chunks"]
    mitre_chunks = hybrid["mitre_chunks"]
    cve_chunks = hybrid["cve_chunks"]
    metadata = [r["metadata"] for r in mitre_results]

    # ── similar threats from MITRE results ───────────────────────────────
    similar_threats = []
    seen = set()
    for result in mitre_results:
        tid = result["metadata"].get("threat_id", "unknown")
        if tid not in seen:
            seen.add(tid)
            similar_threats.append(
                SimilarThreat(
                    threat_id=tid,
                    name=result["metadata"].get("name", tid),
                    score=round(result["score"], 4),
                    chunk_preview=result["chunk"][:150] + "..."
                    if len(result["chunk"]) > 150
                    else result["chunk"],
                )
            )

    threat_id = body.threat_id or (
        metadata[0].get("threat_id", "General") if metadata else "General"
    )
    threat_name = (
        metadata[0].get("name", body.query[:80]) if metadata else body.query[:80]
    )

    # ── build enriched context for LLM ───────────────────────────────────
    rag_context = mitre_chunks.copy()
    if cve_chunks:
        rag_context.append(
            "RELATED CVEs FROM NVD:\n" + "\n".join(cve_chunks)
        )

    analysis, _ = llm_svc.analyze_threat(
        threat_id=threat_id,
        threat_name=threat_name,
        threat_description=mitre_chunks[0] if mitre_chunks else body.query,
        rag_context=rag_context,
        analyst_query=body.query,
    )

    total_latency = (time.perf_counter() - total_start) * 1000
    logger.info(
        "intel_query_complete",
        threat_id=threat_id,
        mitre_chunks=len(mitre_chunks),
        cve_chunks=len(cve_chunks),
        latency_ms=round(total_latency, 2),
    )

    return IntelQueryResponse(
        query=body.query,
        analysis=analysis,
        retrieved_chunks=chunks,
        similar_threats=similar_threats,
        sources=[f"{r['metadata'].get('threat_id','')} - {r['metadata'].get('name','')} (score: {round(r['score'],3)})" for r in mitre_results],
        model_used=settings.llm_model,
        num_chunks_retrieved=len(chunks),
        latency_ms=round(total_latency, 2),
        rag_ready=rag_svc.is_ready,
    )

@router.post("/intel/stream")
async def stream_threat_intel(
    body: IntelQueryRequest,
    rag_svc: RAGService = Depends(get_rag_service),
    llm_svc: LLMService = Depends(get_llm_service),
):
    from fastapi.responses import StreamingResponse
    hybrid = rag_svc.retrieve_with_cves(query=body.query, top_k=body.top_k, max_cves=3)
    mitre_chunks = hybrid["mitre_chunks"]
    cve_chunks = hybrid["cve_chunks"]
    rag_context = mitre_chunks.copy()
    if cve_chunks:
        rag_context.append("RELATED CVEs FROM NVD:\n" + "\n".join(cve_chunks))
    metadata = [r["metadata"] for r in hybrid["mitre_results"]]
    threat_id = metadata[0].get("threat_id", "General") if metadata else "General"
    threat_name = metadata[0].get("name", body.query[:80]) if metadata else body.query[:80]

    def token_stream():
        for token in llm_svc.stream_analyze_threat(
            threat_id=threat_id,
            threat_name=threat_name,
            threat_description=mitre_chunks[0] if mitre_chunks else body.query,
            rag_context=rag_context,
            analyst_query=body.query,
        ):
            yield token

    return StreamingResponse(token_stream(), media_type="text/plain")


@router.get("/intel/status")
async def get_index_status(rag_svc: RAGService = Depends(get_rag_service)):
    return {
        "is_ready": rag_svc.is_ready,
        "num_vectors": rag_svc.num_vectors,
        "embedding_model": settings.embedding_model,
        "vector_backend": "pinecone" if settings.use_pinecone else "faiss",
    }


@router.post("/intel/similar")
async def find_similar_threats(
    query: str,
    top_k: int = 10,
    rag_svc: RAGService = Depends(get_rag_service),
):
    if not rag_svc.is_ready:
        raise HTTPException(status_code=503, detail="Vector store not ready. Run build_vector_store.py first.")

    results = rag_svc.retrieve(query=query, top_k=top_k)
    return {
        "query": query,
        "results": [
            {
                "threat_id": r["metadata"].get("threat_id"),
                "score": round(r["score"], 4),
                "preview": r["chunk"][:200],
                "source": r["metadata"].get("source", "MITRE ATT&CK"),
            }
            for r in results
        ],
        "num_results": len(results),
    }


