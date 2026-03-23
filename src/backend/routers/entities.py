from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from configs.logging_config import get_logger
from configs.settings import settings
from src.backend.models.entity import EntityBase, EntityRead, EntityEnrichRequest, EntityEnrichResponse, EntityRelationship
from src.backend.services.llm_service import LLMService, get_llm_service

logger = get_logger(__name__)
router = APIRouter()

_entities: dict[str, dict] = {}


@router.get("/entities")
async def list_entities(entity_type: str | None = None, limit: int = 50):
    entities = list(_entities.values())
    if entity_type:
        entities = [e for e in entities if e.get("entity_type") == entity_type]
    return {"entities": entities[-limit:], "total": len(entities)}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    if entity_id not in _entities:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return _entities[entity_id]


@router.post("/entities", response_model=EntityRead, status_code=201)
async def create_entity(body: EntityBase):
    if body.entity_id in _entities:
        raise HTTPException(status_code=409, detail=f"Entity '{body.entity_id}' already exists")
    entity = {
        **body.model_dump(),
        "id": len(_entities) + 1,
        "ingested_at": datetime.now(timezone.utc),
        "risk_score": 0.0,
        "relationships": [],
    }
    _entities[body.entity_id] = entity
    logger.info("entity_created", entity_id=body.entity_id, type=body.entity_type)
    return EntityRead(**entity)


@router.post("/entities/enrich", response_model=EntityEnrichResponse)
async def enrich_entity(
    body: EntityEnrichRequest,
    llm_svc: LLMService = Depends(get_llm_service),
):
    if body.entity_id not in _entities:
        raise HTTPException(status_code=404, detail=f"Entity '{body.entity_id}' not found")

    entity = _entities[body.entity_id]
    profile, latency = llm_svc.generate_entity_profile(
        entity_id=entity["entity_id"],
        entity_name=entity["name"],
        entity_type=entity["entity_type"],
        description=entity["description"],
        associated_techniques=entity.get("associated_techniques", []),
    )

    logger.info("entity_enriched", entity_id=body.entity_id, latency_ms=round(latency, 2))

    return EntityEnrichResponse(
        entity_id=entity["entity_id"],
        name=entity["name"],
        threat_profile=profile,
        top_techniques=entity.get("associated_techniques", [])[:5],
        recommended_detections=[
            "Enable process creation audit logging",
            "Monitor for LOLBin usage",
            "Hunt for lateral movement indicators",
        ],
        model_used=settings.llm_model,
        latency_ms=round(latency, 2),
    )


@router.post("/entities/{entity_id}/relationships", status_code=201)
async def add_relationship(entity_id: str, body: EntityRelationship):
    if entity_id not in _entities:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    _entities[entity_id]["relationships"].append(body.model_dump())
    logger.info("relationship_added", source=entity_id, target=body.target_entity_id, type=body.relationship_type)
    return {"status": "added", "relationship": body.model_dump()}


@router.delete("/entities/{entity_id}", status_code=204)
async def delete_entity(entity_id: str):
    if entity_id not in _entities:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    del _entities[entity_id]