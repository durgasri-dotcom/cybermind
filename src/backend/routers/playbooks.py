from __future__ import annotations

import re
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from configs.logging_config import get_logger
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

_playbooks: dict[int, dict] = {}
_counter = 0


@router.get("/playbooks")
async def list_playbooks(status: str | None = None, limit: int = 20):
    playbooks = list(_playbooks.values())
    if status:
        playbooks = [p for p in playbooks if p["status"] == status]
    return {"playbooks": playbooks[-limit:], "total": len(playbooks)}


@router.get("/playbooks/{playbook_id}", response_model=PlaybookRead)
async def get_playbook(playbook_id: int):
    if playbook_id not in _playbooks:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    return PlaybookRead(**_playbooks[playbook_id])


@router.post("/playbooks/generate", response_model=PlaybookRead)
async def generate_playbook(
    body: PlaybookGenerateRequest,
    llm_svc: LLMService = Depends(get_llm_service),
    rag_svc: RAGService = Depends(get_rag_service),
):
    global _counter
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

    _counter += 1
    playbook = {
        "id": _counter,
        "threat_id": body.threat_id,
        "title": f"IR Playbook: {body.threat_id}",
        "objective": f"Contain, eradicate, and recover from {body.threat_id} incident",
        "steps": [s.model_dump() for s in steps],
        "status": PlaybookStatus.ACTIVE,
        "tags": ["auto-generated", body.threat_id],
        "generated_at": datetime.now(UTC),
        "generated_by": "CyberMind",
        "version": 1,
    }
    _playbooks[_counter] = playbook

    logger.info("playbook_generated", id=_counter, threat_id=body.threat_id, steps=len(steps), latency_ms=round(elapsed, 2))
    return PlaybookRead(**playbook)


@router.delete("/playbooks/{playbook_id}", status_code=204)
async def delete_playbook(playbook_id: int):
    if playbook_id not in _playbooks:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    del _playbooks[playbook_id]


def _parse_steps(raw: str) -> list[PlaybookStep]:
    steps = []
    lines = raw.split("\n")
    current: dict | None = None
    current_notes: list[str] = []
    step_num = 0

    for line in lines:
        match = re.match(r"^(?:\*{0,2})?(?:Step\s+)?(\d+)[.:)\]]\s*\*{0,2}\s*(.+)", line.strip(), re.IGNORECASE)
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