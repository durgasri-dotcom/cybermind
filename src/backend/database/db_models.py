from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.sql import func

from .engine import Base


class AlertDB(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    threat_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(10), default="P3")
    status = Column(String(50), default="open")
    source_ip = Column(String(100), nullable=True)
    target_asset = Column(String(255), nullable=True)
    indicators = Column(JSON, default=list)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    playbook_id = Column(Integer, nullable=True)


class PlaybookDB(Base):
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    threat_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    steps = Column(JSON, default=list)
    status = Column(String(50), default="draft")
    tags = Column(JSON, default=list)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(String(100), default="CyberMind")
    version = Column(Integer, default=1)


class EntityDB(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    aliases = Column(JSON, default=list)
    associated_techniques = Column(JSON, default=list)
    targeted_sectors = Column(JSON, default=list)
    targeted_countries = Column(JSON, default=list)
    source = Column(String(255), default="MITRE ATT&CK")
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    risk_score = Column(Float, default=0.0)
    relationships = Column(JSON, default=list)