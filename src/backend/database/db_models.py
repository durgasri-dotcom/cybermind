from __future__ import annotations

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
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


class CveDB(Base):
    __tablename__ = "cves"

    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String(20), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    cvss_score = Column(Float, nullable=True)
    cvss_severity = Column(String(20), nullable=True)
    cvss_vector = Column(String(255), nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    modified_date = Column(DateTime(timezone=True), nullable=True)
    cwe_ids = Column(JSON, default=list)
    affected_products = Column(JSON, default=list)
    mitre_techniques = Column(JSON, default=list)
    risk_score = Column(Float, default=0.0)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_nvd = Column(JSON, default=dict)

class RequestLogDB(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    method = Column(String(10), nullable=False)           
    path = Column(String(500), nullable=False)            
    status_code = Column(Integer, nullable=False)         
    latency_ms = Column(Float, nullable=False)            
    client_ip = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
class EmbeddingDB(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(255), nullable=False, unique=True, index=True)
    threat_id = Column(String(255), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    vector = Column(JSON, nullable=False)
    source = Column(String(255), default="MITRE ATT&CK")
    metadata_ = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
