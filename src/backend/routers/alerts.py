from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from configs.logging_config import get_logger
from configs.settings import settings
from src.backend.models.alert import AlertCreate, AlertRead, AlertStatus, AlertTriage, AlertPriority
from src.backend.services.llm_service import LLMService, get_llm_service

logger = get_logger(__name__)
router = APIRouter()

_alerts: dict[int, dict] = {}
_counter = 0


@router.get("/alerts")
async def list_alerts(status: str | None = None, limit: int = 50):
    alerts = list(_alerts.values())
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    return {"alerts": alerts[-limit:], "total": len(alerts)}


@router.post("/alerts", response_model=AlertRead, status_code=201)
async def create_alert(body: AlertCreate):
    global _counter
    _counter += 1
    alert = {
        **body.model_dump(),
        "id": _counter,
        "triggered_at": datetime.now(timezone.utc),
        "resolved_at": None,
        "assigned_to": None,
        "playbook_id": None,
    }
    _alerts[_counter] = alert
    logger.info("alert_created", alert_id=_counter, threat_id=body.threat_id, priority=body.priority)
    return AlertRead(**alert)


@router.get("/alerts/{alert_id}", response_model=AlertRead)
async def get_alert(alert_id: int):
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return AlertRead(**_alerts[alert_id])


@router.post("/alerts/{alert_id}/triage", response_model=AlertTriage)
async def triage_alert(
    alert_id: int,
    llm_svc: LLMService = Depends(get_llm_service),
):
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    alert = _alerts[alert_id]
    analysis, _ = llm_svc.triage_alert(
        alert_title=alert["title"],
        alert_description=alert["description"],
        threat_context=f"Threat ID: {alert['threat_id']}",
        indicators=alert.get("indicators", []),
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


@router.patch("/alerts/{alert_id}/status")
async def update_alert_status(alert_id: int, status: AlertStatus):
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    _alerts[alert_id]["status"] = status
    if status == AlertStatus.RESOLVED:
        _alerts[alert_id]["resolved_at"] = datetime.now(timezone.utc)
    logger.info("alert_status_updated", alert_id=alert_id, status=status)
    return {"alert_id": alert_id, "status": status}


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(alert_id: int):
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    del _alerts[alert_id]