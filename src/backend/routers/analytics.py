from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.backend.database.db_models import RequestLogDB
from src.backend.database.engine import get_db

router = APIRouter()


@router.get("/analytics/requests")
async def request_stats(db: Session = Depends(get_db)):
    total = db.query(RequestLogDB).count()
    avg_latency = db.query(func.avg(RequestLogDB.latency_ms)).scalar()
    by_method = (
        db.query(RequestLogDB.method, func.count(RequestLogDB.id))
        .group_by(RequestLogDB.method)
        .all()
    )
    by_status = (
        db.query(RequestLogDB.status_code, func.count(RequestLogDB.id))
        .group_by(RequestLogDB.status_code)
        .all()
    )
    by_path = (
        db.query(RequestLogDB.path, func.count(RequestLogDB.id))
        .group_by(RequestLogDB.path)
        .order_by(func.count(RequestLogDB.id).desc())
        .limit(10)
        .all()
    )
    slowest = (
        db.query(RequestLogDB.path, RequestLogDB.method, RequestLogDB.latency_ms)
        .order_by(RequestLogDB.latency_ms.desc())
        .limit(5)
        .all()
    )
    return {
        "total_requests": total,
        "avg_latency_ms": round(avg_latency or 0.0, 2),
        "by_method": {method: count for method, count in by_method},
        "by_status_code": {str(code): count for code, count in by_status},
        "top_endpoints": [
            {"path": path, "count": count} for path, count in by_path
        ],
        "slowest_endpoints": [
            {"path": path, "method": method, "latency_ms": round(latency, 2)}
            for path, method, latency in slowest
        ],
    }


@router.get("/analytics/requests/recent")
async def recent_requests(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(RequestLogDB)
        .order_by(RequestLogDB.timestamp.desc())
        .limit(limit)
        .all()
    )
    return {
        "requests": [
            {
                "id": r.id,
                "method": r.method,
                "path": r.path,
                "status_code": r.status_code,
                "latency_ms": r.latency_ms,
                "client_ip": r.client_ip,
                "timestamp": r.timestamp,
            }
            for r in rows
        ],
        "total": len(rows),
    }