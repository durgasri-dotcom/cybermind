from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    THREAT_ACTOR = "threat_actor"
    MALWARE = "malware"
    TOOL = "tool"
    CAMPAIGN = "campaign"
    INFRASTRUCTURE = "infrastructure"


class EntityRelationship(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class EntityBase(BaseModel):
    entity_id: str
    name: str
    entity_type: EntityType
    description: str
    aliases: list[str] = Field(default_factory=list)
    associated_techniques: list[str] = Field(default_factory=list)
    targeted_sectors: list[str] = Field(default_factory=list)
    targeted_countries: list[str] = Field(default_factory=list)
    source: str = "MITRE ATT&CK"


class EntityRead(EntityBase):
    id: int
    ingested_at: datetime
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relationships: list[EntityRelationship] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class EntityEnrichRequest(BaseModel):
    entity_id: str
    include_ttp_analysis: bool = True
    include_mitigations: bool = True


class EntityEnrichResponse(BaseModel):
    entity_id: str
    name: str
    threat_profile: str
    top_techniques: list[str]
    recommended_detections: list[str]
    model_used: str
    latency_ms: float