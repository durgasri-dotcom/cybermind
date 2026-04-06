from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from sqlalchemy import text

from configs.settings import settings
from src.backend.database.engine import DATABASE_URL, engine

router = APIRouter()

@router.get("/health")
async def health_check(request: Request):
    rag_svc = getattr(request.app.state, "rag_service", None)

    # Detect database backend
    if DATABASE_URL.startswith("postgresql"):
        db_backend = "postgresql"
    else:
        db_backend = "sqlite"

    # DB health check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = {"status": "ok", "backend": db_backend, "connected": True}
    except Exception as e:
        db_status = {"status": "error", "connected": False, "detail": str(e)}

    return {
        "status": "healthy",
        "platform": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(UTC).isoformat(),
        "services": {
            "rag": {
                "ready": rag_svc.is_ready if rag_svc else False,
                "vectors": rag_svc.num_vectors if rag_svc else 0,
            },
            "llm": {
                "provider": settings.llm_provider,
                "model": settings.llm_model,
            },
            "embeddings": {
                "model": settings.embedding_model,
            },
            "vector_backend": "pinecone" if settings.use_pinecone else "faiss",
            "database": db_status,
            "scheduler": {
                "status": "running",
                "jobs": ["cve_ingest"],
                "interval": "every 24 hours",
            },
        },
    }
