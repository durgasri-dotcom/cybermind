from __future__ import annotations
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from configs.settings import settings
from configs.logging_config import configure_logging, get_logger
from src.backend.services.rag_service import get_rag_service
from src.backend.services.llm_service import get_llm_service
from src.backend.services.embedding_service import get_embedding_service
from src.backend.routers import threats, intel, alerts, playbooks, entities, health

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("cybermind_startup", version=settings.app_version)
    start = time.perf_counter()

    embedding_svc = get_embedding_service()
    rag_svc = get_rag_service()
    rag_svc.load_index()
    llm_svc = get_llm_service()

    app.state.embedding_service = embedding_svc
    app.state.rag_service = rag_svc
    app.state.llm_service = llm_svc

    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "cybermind_ready",
        faiss_vectors=rag_svc.num_vectors,
        rag_ready=rag_svc.is_ready,
        startup_ms=round(elapsed, 2),
    )

    yield

    logger.info("cybermind_shutdown")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{elapsed:.2f}ms"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        path=str(request.url),
        method=request.method,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "Contact the CyberMind team",
        },
    )


prefix = settings.api_prefix

app.include_router(health.router,    prefix=prefix, tags=["Health"])
app.include_router(threats.router,   prefix=prefix, tags=["Threats"])
app.include_router(intel.router,     prefix=prefix, tags=["Intel"])
app.include_router(alerts.router,    prefix=prefix, tags=["Alerts"])
app.include_router(playbooks.router, prefix=prefix, tags=["Playbooks"])
app.include_router(entities.router,  prefix=prefix, tags=["Entities"])


@app.get("/", include_in_schema=False)
async def root():
    return {
        "platform": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": f"{prefix}/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )