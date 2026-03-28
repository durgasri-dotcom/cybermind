from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from configs.logging_config import get_logger
from configs.settings import settings
from src.backend.database.engine import get_db
from src.backend.database.db_models import EntityDB
from src.backend.middleware.auth import verify_api_key
from src.backend.models.entity import (
    EntityBase,
    EntityEnrichRequest,
    EntityEnrichResponse,
    EntityRead,
    EntityRelationship,
)
from src.backend.services.llm_service import LLMService, get_llm_service

logger = get_logger(__name__)
router = APIRouter()


def _row_to_dict(row: EntityDB) -> dict:
    return {
        "entity_id": row.entity_id,
        "name": row.name,
        "entity_type": row.entity_type,
        "description": row.description,
        "aliases": row.aliases or [],
        "associated_techniques": row.associated_techniques or [],
        "targeted_sectors": row.targeted_sectors or [],
        "targeted_countries": row.targeted_countries or [],
        "source": row.source,
        "id": row.id,
        "ingested_at": row.ingested_at,
        "risk_score": row.risk_score,
        "relationships": row.relationships or [],
    }


@router.get("/entities")
async def list_entities(
    entity_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(EntityDB).order_by(EntityDB.ingested_at.desc())
    if entity_type:
        q = q.filter(EntityDB.entity_type == entity_type)
    rows = q.limit(limit).all()
    return {"entities": [_row_to_dict(r) for r in rows], "total": len(rows)}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str, db: Session = Depends(get_db)):
    row = db.query(EntityDB).filter(EntityDB.entity_id == entity_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return _row_to_dict(row)


@router.post("/entities", response_model=EntityRead, status_code=201,
             dependencies=[Depends(verify_api_key)])
async def create_entity(body: EntityBase, db: Session = Depends(get_db)):
    existing = db.query(EntityDB).filter(EntityDB.entity_id == body.entity_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Entity '{body.entity_id}' already exists")
    row = EntityDB(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("entity_created", entity_id=body.entity_id, type=body.entity_type)
    return EntityRead(**_row_to_dict(row))


@router.post("/entities/enrich", response_model=EntityEnrichResponse)
async def enrich_entity(
    body: EntityEnrichRequest,
    db: Session = Depends(get_db),
    llm_svc: LLMService = Depends(get_llm_service),
):
    row = db.query(EntityDB).filter(EntityDB.entity_id == body.entity_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Entity '{body.entity_id}' not found")
    profile, latency = llm_svc.generate_entity_profile(
        entity_id=row.entity_id,
        entity_name=row.name,
        entity_type=row.entity_type,
        description=row.description,
        associated_techniques=row.associated_techniques or [],
    )
    logger.info("entity_enriched", entity_id=body.entity_id, latency_ms=round(latency, 2))
    return EntityEnrichResponse(
        entity_id=row.entity_id,
        name=row.name,
        threat_profile=profile,
        top_techniques=(row.associated_techniques or [])[:5],
        recommended_detections=[
            "Enable process creation audit logging",
            "Monitor for LOLBin usage",
            "Hunt for lateral movement indicators",
        ],
        model_used=settings.llm_model,
        latency_ms=round(latency, 2),
    )


@router.post("/entities/{entity_id}/relationships", status_code=201,
             dependencies=[Depends(verify_api_key)])
async def add_relationship(
    entity_id: str,
    body: EntityRelationship,
    db: Session = Depends(get_db),
):
    row = db.query(EntityDB).filter(EntityDB.entity_id == entity_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    rels = list(row.relationships or [])
    rels.append(body.model_dump())
    row.relationships = rels
    db.commit()
    logger.info("relationship_added", source=entity_id,
                target=body.target_entity_id, type=body.relationship_type)
    return {"status": "added", "relationship": body.model_dump()}


@router.delete("/entities/{entity_id}", status_code=204,
               dependencies=[Depends(verify_api_key)])
async def delete_entity(entity_id: str, db: Session = Depends(get_db)):
    row = db.query(EntityDB).filter(EntityDB.entity_id == entity_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    db.delete(row)
    db.commit()