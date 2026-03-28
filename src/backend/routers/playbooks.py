from __future__ import annotations

import re
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from configs.logging_config import get_logger
from src.backend.database.db_models import PlaybookDB
from src.backend.database.engine import get_db
from src.backend.middleware.auth import verify_api_key
from src.backend.models.playbook import (
    PlaybookGenerateRequest,
    PlaybookRead,
    PlaybookStatus,
    PlaybookStep,
)
from src.backend.services.llm_service import LLMService, get_llm_service
from src.backend.services.rag_service import RAGService, get_rag_service

logger = get_logger(__name__)
router = APIRouter()


def _row_to_dict(row: PlaybookDB) -> dict:
    return {
        "id": row.id,
        "threat_id": row.threat_id,
        "title": row.title,
        "objective": row.objective,
        "steps": row.steps or [],
        "status": row.status,
        "tags": row.tags or [],
        "generated_at": row.generated_at,
        "generated_by": row.generated_by,
        "version": row.version,
    }


@router.get("/playbooks")
async def list_playbooks(
    status: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(PlaybookDB).order_by(PlaybookDB.generated_at.desc())
    if status:
        q = q.filter(PlaybookDB.status == status)
    rows = q.limit(limit).all()
    return {"playbooks": [_row_to_dict(r) for r in rows], "total": len(rows)}


@router.get("/playbooks/{playbook_id}", response_model=PlaybookRead)
async def get_playbook(playbook_id: int, db: Session = Depends(get_db)):
    row = db.query(PlaybookDB).filter(PlaybookDB.id == playbook_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    return PlaybookRead(**_row_to_dict(row))


@router.post("/playbooks/generate", response_model=PlaybookRead,
             dependencies=[Depends(verify_api_key)])
async def generate_playbook(
    body: PlaybookGenerateRequest,
    db: Session = Depends(get_db),
    llm_svc: LLMService = Depends(get_llm_service),
    rag_svc: RAGService = Depends(get_rag_service),
):
    start = time.perf_counter()

    rag_context = rag_svc.retrieve_chunks(
        query=f"incident response {body.threat_id} containment eradication",
        top_k=3,
    )
    alert_context = body.context
    if rag_context:
        alert_context += "\n\nRelevant context:\n" + "\n\n".join(rag_context[:2])

    raw, llm_latency = llm_svc.generate_playbook(
        threat_id=body.threat_id,
        threat_name=body.threat_id,
        alert_context=alert_context,
        available_tools=body.include_tools or [],
    )

    steps = _parse_steps(raw)
    elapsed = (time.perf_counter() - start) * 1000

    row = PlaybookDB(
        threat_id=body.threat_id,
        title=f"IR Playbook: {body.threat_id}",
        objective=f"Contain, eradicate, and recover from {body.threat_id} incident",
        steps=[s.model_dump() for s in steps],
        status=PlaybookStatus.ACTIVE,
        tags=["auto-generated", body.threat_id],
        generated_by="CyberMind",
        version=1,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    logger.info("playbook_generated", id=row.id, threat_id=body.threat_id,
                steps=len(steps), latency_ms=round(elapsed, 2))
    return PlaybookRead(**_row_to_dict(row))


@router.delete("/playbooks/{playbook_id}", status_code=204,
               dependencies=[Depends(verify_api_key)])
async def delete_playbook(playbook_id: int, db: Session = Depends(get_db)):
    row = db.query(PlaybookDB).filter(PlaybookDB.id == playbook_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    db.delete(row)
    db.commit()


# ── helpers (unchanged from original) ────────────────────────────────────────

def _parse_steps(raw: str) -> list[PlaybookStep]:
    steps = []
    lines = raw.split("\n")
    current: dict | None = None
    current_notes: list[str] = []
    step_num = 0

    for line in lines:
        match = re.match(r"^(?:\*{0,2})?(?:Step\s+)?(\d+)[.:)\]]\s*\*{0,2}\s*(.+)",
                         line.strip(), re.IGNORECASE)
        if match:
            if current is not None:
                current["notes"] = " ".join(current_notes).strip()
                steps.append(PlaybookStep(**current))
                current_notes = []
            step_num += 1
            action = match.group(2).strip().rstrip("*").strip()
            current = {
                "step_number": step_num,
                "action": action,
                "responsible_team": _infer_team(action),
                "tools": _infer_tools(action),
                "estimated_minutes": _infer_time(action),
                "notes": "",
            }
        elif current is not None and line.strip():
            current_notes.append(line.strip())

    if current is not None:
        current["notes"] = " ".join(current_notes).strip()
        steps.append(PlaybookStep(**current))

    if not steps:
        steps.append(PlaybookStep(
            step_number=1,
            action="Review and execute AI-generated response plan",
            responsible_team="SOC Tier 1",
            tools=[],
            estimated_minutes=30,
            notes=raw[:500],
        ))
    return steps


def _infer_team(action: str) -> str:
    a = action.lower()
    if any(w in a for w in ["isolate", "block", "contain", "quarantine"]):
        return "SOC Tier 2"
    if any(w in a for w in ["patch", "remediat", "eradicat"]):
        return "IR Team"
    if any(w in a for w in ["notify", "escalat", "report", "ciso"]):
        return "Management"
    if any(w in a for w in ["recover", "restore", "backup"]):
        return "IT Operations"
    return "SOC Tier 1"


def _infer_tools(action: str) -> list[str]:
    mapping = {
        "splunk": "Splunk", "crowdstrike": "CrowdStrike",
        "sentinel": "Microsoft Sentinel", "siem": "SIEM",
        "edr": "EDR", "firewall": "Firewall",
        "dns": "DNS Filter", "email": "Email Gateway",
    }
    return [v for k, v in mapping.items() if k in action.lower()]


def _infer_time(action: str) -> int:
    a = action.lower()
    if any(w in a for w in ["immediately", "isolate", "block"]):
        return 15
    if any(w in a for w in ["investigate", "analyze", "review"]):
        return 60
    if any(w in a for w in ["patch", "restore", "recover"]):
        return 120
    return 30