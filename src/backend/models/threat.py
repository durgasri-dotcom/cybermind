from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ThreatCategory(str, Enum):
    INITIAL_ACCESS = "Initial Access"
    EXECUTION = "Execution"
    PERSISTENCE = "Persistence"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    DEFENSE_EVASION = "Defense Evasion"
    CREDENTIAL_ACCESS = "Credential Access"
    DISCOVERY = "Discovery"
    LATERAL_MOVEMENT = "Lateral Movement"
    COLLECTION = "Collection"
    EXFILTRATION = "Exfiltration"
    IMPACT = "Impact"
    COMMAND_AND_CONTROL = "Command and Control"
    CVE = "CVE"
    UNKNOWN = "Unknown"


class ThreatBase(BaseModel):
    threat_id: str = Field(..., description="MITRE ATT&CK ID e.g. T1059 or CVE ID")
    name: str
    description: str
    category: ThreatCategory = ThreatCategory.UNKNOWN
    severity: SeverityLevel = SeverityLevel.UNKNOWN
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = "MITRE ATT&CK"
    tags: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)


class ThreatCreate(ThreatBase):
    pass


class ThreatRead(ThreatBase):
    id: int
    ingested_at: datetime
    embedding_id: Optional[str] = None

    model_config = {"from_attributes": True}


class ThreatSummary(BaseModel):
    threat_id: str
    name: str
    category: ThreatCategory
    severity: SeverityLevel
    risk_score: float
    source: str


class ThreatAnalysis(BaseModel):
    threat_id: str
    query: str
    analysis: str
    retrieved_chunks: list[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    model_used: str
    latency_ms: float