from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from configs.logging_config import configure_logging, get_logger
from configs.settings import settings
from src.backend.middleware.request_logger import request_logging_middleware
from src.backend.routers import alerts, analytics, cves, entities, health, intel, playbooks, threats
from src.backend.services.llm_service import get_llm_service
from src.backend.services.rag_service import get_rag_service
from src.backend.database.engine import SessionLocal
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("cybermind_startup", version=settings.app_version)
    start = time.perf_counter()

    # ── DB init ───────────────────────────────────────────────────────────────
    from src.backend.database import db_models  # noqa: F401
    from src.backend.database.engine import Base, engine
    Base.metadata.create_all(bind=engine)
    logger.info("database_ready", backend="sqlite")

    # ── startup CVE ingest (repopulates DB after Render cold start) ───────────
    try:
        from src.backend.services.cve_service import get_cve_service
        from src.backend.database.db_models import CveDB
        cve_count = SessionLocal().query(CveDB).count()
        if cve_count == 0:
            logger.info("startup_cve_ingest_start", reason="empty_database")
            cve_svc = get_cve_service()
            cves = cve_svc.fetch_recent(days=7, max_results=50)
            db = SessionLocal()
            ingested = 0
            for cve_data in cves:
                cve_id = cve_data.get("cve_id")
                if cve_id and not db.query(CveDB).filter(CveDB.cve_id == cve_id).first():
                    db.add(CveDB(**cve_data))
                    ingested += 1
            db.commit()
            db.close()
            logger.info("startup_cve_ingest_complete", ingested=ingested)
        else:
            logger.info("startup_cve_ingest_skipped", existing_cves=cve_count)
    except Exception as e:
        logger.warning("startup_cve_ingest_failed", error=str(e))

    # ── scheduler ─────────────────────────────────────────────────────────────
    from apscheduler.triggers.interval import IntervalTrigger

    from src.backend.services.scheduler import get_scheduler, ingest_cves_job
    scheduler = get_scheduler()
    scheduler.add_job(
        ingest_cves_job,
        trigger=IntervalTrigger(hours=24),
        id="cve_ingest",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("scheduler_started", jobs=["cve_ingest"], interval_hours=24)

    # ── service startup ───────────────────────────────────────────────────────
    rag_svc = get_rag_service()
    rag_svc.load_index()
    llm_svc = get_llm_service()
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

    scheduler.shutdown()
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
app.middleware("http")(request_logging_middleware)
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
app.include_router(cves.router, prefix=prefix, tags=["CVEs"])
app.include_router(analytics.router, prefix=prefix, tags=["Analytics"])

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