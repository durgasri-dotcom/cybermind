from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from configs.logging_config import get_logger
from configs.settings import settings
from src.backend.database.engine import get_db
from src.backend.database.db_models import AlertDB
from src.backend.middleware.auth import verify_api_key
from src.backend.models.alert import AlertCreate, AlertPriority, AlertRead, AlertStatus, AlertTriage
from src.backend.services.llm_service import LLMService, get_llm_service

logger = get_logger(__name__)
router = APIRouter()


def _row_to_dict(row: AlertDB) -> dict:
    return {
        "id": row.id,
        "threat_id": row.threat_id,
        "title": row.title,
        "description": row.description,
        "priority": row.priority,
        "status": row.status,
        "source_ip": row.source_ip,
        "target_asset": row.target_asset,
        "indicators": row.indicators or [],
        "triggered_at": row.triggered_at,
        "resolved_at": row.resolved_at,
        "assigned_to": row.assigned_to,
        "playbook_id": row.playbook_id,
    }


@router.get("/alerts")
async def list_alerts(
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(AlertDB).order_by(AlertDB.triggered_at.desc())
    if status:
        q = q.filter(AlertDB.status == status)
    rows = q.limit(limit).all()
    return {"alerts": [_row_to_dict(r) for r in rows], "total": len(rows)}


@router.post("/alerts", response_model=AlertRead, status_code=201,
             dependencies=[Depends(verify_api_key)])
async def create_alert(body: AlertCreate, db: Session = Depends(get_db)):
    row = AlertDB(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("alert_created", alert_id=row.id, threat_id=body.threat_id, priority=body.priority)
    return AlertRead(**_row_to_dict(row))


@router.get("/alerts/{alert_id}", response_model=AlertRead)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    row = db.query(AlertDB).filter(AlertDB.id == alert_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return AlertRead(**_row_to_dict(row))


@router.post("/alerts/{alert_id}/triage", response_model=AlertTriage)
async def triage_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    llm_svc: LLMService = Depends(get_llm_service),
):
    row = db.query(AlertDB).filter(AlertDB.id == alert_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    analysis, _ = llm_svc.triage_alert(
        alert_title=row.title,
        alert_description=row.description,
        threat_context=f"Threat ID: {row.threat_id}",
        indicators=row.indicators or [],
    )
    logger.info("alert_triaged", alert_id=alert_id, model=settings.llm_model)
    return AlertTriage(
        alert_id=alert_id,
        priority_recommendation=AlertPriority.P2,
        reasoning=analysis,
        suggested_actions=["Isolate affected host", "Review SIEM logs", "Notify SOC lead"],
        escalate=True,
        model_used=settings.llm_model,
    )


@router.patch("/alerts/{alert_id}/status",
              dependencies=[Depends(verify_api_key)])
async def update_alert_status(
    alert_id: int,
    status: AlertStatus,
    db: Session = Depends(get_db),
):
    row = db.query(AlertDB).filter(AlertDB.id == alert_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    row.status = status
    if status == AlertStatus.RESOLVED:
        row.resolved_at = datetime.now(UTC)
    db.commit()
    logger.info("alert_status_updated", alert_id=alert_id, status=status)
    return {"alert_id": alert_id, "status": status}


@router.delete("/alerts/{alert_id}", status_code=204,
               dependencies=[Depends(verify_api_key)])
async def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    row = db.query(AlertDB).filter(AlertDB.id == alert_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    db.delete(row)
    db.commit()