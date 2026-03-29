from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from configs.logging_config import get_logger

logger = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def ingest_cves_job() -> None:
    """Scheduled job — fetches recent CVEs from NVD and persists to SQLite."""
    try:
        from src.backend.database.db_models import CveDB
        from src.backend.database.engine import SessionLocal
        from src.backend.services.cve_service import get_cve_service

        logger.info("scheduled_cve_ingest_start")
        cve_svc = get_cve_service()
        cves = cve_svc.fetch_recent(days=1, max_results=50)

        db = SessionLocal()
        ingested, updated, skipped = 0, 0, 0

        for cve_data in cves:
            cve_id = cve_data.get("cve_id")
            if not cve_id:
                skipped += 1
                continue
            existing = db.query(CveDB).filter(CveDB.cve_id == cve_id).first()
            if existing:
                for k, v in cve_data.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.add(CveDB(**cve_data))
                ingested += 1

        db.commit()
        db.close()

        logger.info(
            "scheduled_cve_ingest_complete",
            ingested=ingested,
            updated=updated,
            skipped=skipped,
            total=ingested + updated,
        )
    except Exception as e:
        logger.error("scheduled_cve_ingest_failed", error=str(e))