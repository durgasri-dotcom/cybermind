from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query

from configs.logging_config import get_logger
from src.backend.models.threat import SeverityLevel, ThreatCreate, ThreatRead
from src.backend.services.threat_scoring import score_to_severity

logger = get_logger(__name__)
router = APIRouter()

_threats: dict[int, dict] = {}
_counter = 0


def load_threats_from_gold() -> None:
    global _threats, _counter
    import json
    from pathlib import Path
    p = Path("data/gold/mitre_threats_enriched.json")
    if not p.exists():
        return
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        _counter += 1
        _threats[_counter] = {
            **item,
            "id": _counter,
            "ingested_at": "2026-01-01T00:00:00+00:00",
            "embedding_id": None,
        }
    logger.info("threats_loaded_from_gold", count=len(_threats))


load_threats_from_gold()


@router.get("/threats")
async def list_threats(
    severity: str | None = Query(None),
    source: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    threats = list(_threats.values())
    if severity:
        threats = [t for t in threats if t["severity"] == severity]
    if source:
        threats = [t for t in threats if t["source"] == source]
    return {"threats": threats[-limit:], "total": len(threats)}


@router.post("/threats", response_model=ThreatRead, status_code=201)
async def create_threat(body: ThreatCreate):
    global _counter
    _counter += 1
    threat = {
        **body.model_dump(),
        "id": _counter,
        "severity": score_to_severity(body.risk_score).value,
        "ingested_at": datetime.now(UTC),
        "embedding_id": None,
    }
    _threats[_counter] = threat
    logger.info("threat_created", threat_id=body.threat_id, risk_score=body.risk_score)
    return ThreatRead(**threat)


@router.get("/threats/summary/by-severity")
async def threats_by_severity():
    counts = {s.value: 0 for s in SeverityLevel}
    for t in _threats.values():
        sev = t.get("severity", SeverityLevel.UNKNOWN.value)
        counts[sev] = counts.get(sev, 0) + 1
    return {"by_severity": counts, "total": len(_threats)}


@router.get("/threats/{threat_id}", response_model=ThreatRead)
async def get_threat(threat_id: str):
    match = next((t for t in _threats.values() if t["threat_id"] == threat_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Threat '{threat_id}' not found")
    return ThreatRead(**match)


@router.delete("/threats/{threat_id}", status_code=204)
async def delete_threat(threat_id: str):
    match = next((k for k, t in _threats.items() if t["threat_id"] == threat_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Threat '{threat_id}' not found")
    del _threats[match]