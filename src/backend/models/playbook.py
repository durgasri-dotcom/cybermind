from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PlaybookStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class PlaybookStep(BaseModel):
    step_number: int
    action: str
    responsible_team: str
    tools: list[str] = Field(default_factory=list)
    estimated_minutes: int = 15
    notes: str = ""


class PlaybookBase(BaseModel):
    threat_id: str
    title: str
    objective: str
    steps: list[PlaybookStep] = Field(default_factory=list)
    status: PlaybookStatus = PlaybookStatus.DRAFT
    tags: list[str] = Field(default_factory=list)


class PlaybookCreate(PlaybookBase):
    pass


class PlaybookRead(PlaybookBase):
    id: int
    generated_at: datetime
    generated_by: str = "CyberMind"
    version: int = 1

    model_config = {"from_attributes": True}


class PlaybookGenerateRequest(BaseModel):
    threat_id: str
    alert_id: int | None = None
    context: str = ""
    include_tools: list[str] = Field(default_factory=list)