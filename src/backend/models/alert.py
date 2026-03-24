from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AlertStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class AlertPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class AlertBase(BaseModel):
    threat_id: str
    title: str
    description: str
    priority: AlertPriority = AlertPriority.P3
    status: AlertStatus = AlertStatus.OPEN
    source_ip: str | None = None
    target_asset: str | None = None
    indicators: list[str] = Field(default_factory=list)


class AlertCreate(AlertBase):
    pass


class AlertRead(AlertBase):
    id: int
    triggered_at: datetime
    resolved_at: datetime | None = None
    assigned_to: str | None = None
    playbook_id: int | None = None

    model_config = {"from_attributes": True}


class AlertTriage(BaseModel):
    alert_id: int
    priority_recommendation: AlertPriority
    reasoning: str
    suggested_actions: list[str]
    escalate: bool
    model_used: str