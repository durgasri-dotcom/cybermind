from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from configs.logging_config import get_logger
from src.backend.database.db_models import CveDB
from src.backend.database.engine import get_db
from src.backend.middleware.auth import verify_api_key
from src.backend.services.cve_service import CVEService, get_cve_service

logger = get_logger(__name__)
router = APIRouter()


def _row_to_dict(row: CveDB) -> dict:
    return {
        "id": row.id,
        "cve_id": row.cve_id,
        "description": row.description,
        "cvss_score": row.cvss_score,
        "cvss_severity": row.cvss_severity,
        "cvss_vector": row.cvss_vector,
        "published_date": row.published_date,
        "modified_date": row.modified_date,
        "cwe_ids": row.cwe_ids or [],
        "affected_products": row.affected_products or [],
        "mitre_techniques": row.mitre_techniques or [],
        "risk_score": row.risk_score,
        "ingested_at": row.ingested_at,
    }


@router.get("/cves")
async def list_cves(
    severity: str | None = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(CveDB).order_by(CveDB.cvss_score.desc().nullslast())
    if severity:
        q = q.filter(CveDB.cvss_severity == severity.upper())
    rows = q.limit(limit).all()
    return {"cves": [_row_to_dict(r) for r in rows], "total": len(rows)}


@router.get("/cves/stats")
async def cve_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.query(CveDB).count()
    by_severity = (
        db.query(CveDB.cvss_severity, func.count(CveDB.id))
        .group_by(CveDB.cvss_severity)
        .all()
    )
    avg_score = db.query(func.avg(CveDB.cvss_score)).scalar()
    critical_count = db.query(CveDB).filter(CveDB.cvss_severity == "CRITICAL").count()
    return {
        "total": total,
        "critical": critical_count,
        "avg_cvss_score": round(avg_score or 0.0, 2),
        "by_severity": {sev: count for sev, count in by_severity if sev},
    }


@router.get("/cves/{cve_id}")
async def get_cve(cve_id: str, db: Session = Depends(get_db)):
    row = db.query(CveDB).filter(CveDB.cve_id == cve_id.upper()).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"CVE '{cve_id}' not found")
    return _row_to_dict(row)


@router.post("/cves/ingest/recent", dependencies=[Depends(verify_api_key)])
async def ingest_recent_cves(
    days: int = Query(7, ge=1, le=30),
    max_results: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    cve_svc: CVEService = Depends(get_cve_service),
):
    cves = cve_svc.fetch_recent(days=days, max_results=max_results)
    return _upsert_cves(cves, db)


@router.post("/cves/ingest/severity", dependencies=[Depends(verify_api_key)])
async def ingest_by_severity(
    severity: str = Query(..., description="LOW, MEDIUM, HIGH, CRITICAL"),
    max_results: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    cve_svc: CVEService = Depends(get_cve_service),
):
    cves = cve_svc.fetch_by_severity(severity=severity, max_results=max_results)
    return _upsert_cves(cves, db)


@router.post("/cves/ingest/keyword", dependencies=[Depends(verify_api_key)])
async def ingest_by_keyword(
    keyword: str = Query(..., description="e.g. apache, windows, sql injection"),
    max_results: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    cve_svc: CVEService = Depends(get_cve_service),
):
    cves = cve_svc.fetch_by_keyword(keyword=keyword, max_results=max_results)
    return _upsert_cves(cves, db)


@router.delete("/cves/{cve_id}", status_code=204, dependencies=[Depends(verify_api_key)])
async def delete_cve(cve_id: str, db: Session = Depends(get_db)):
    row = db.query(CveDB).filter(CveDB.cve_id == cve_id.upper()).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"CVE '{cve_id}' not found")
    db.delete(row)
    db.commit()


# ── helper ────────────────────────────────────────────────────────────────────

def _upsert_cves(cves: list[dict], db: Session) -> dict:
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
    logger.info("cves_upserted", ingested=ingested, updated=updated, skipped=skipped)
    return {"ingested": ingested, "updated": updated, "skipped": skipped, "total": ingested + updated}