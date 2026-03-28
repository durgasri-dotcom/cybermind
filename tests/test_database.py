from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database.engine import Base
from src.backend.database import db_models  # noqa: F401
from src.backend.database.db_models import AlertDB, EntityDB, PlaybookDB


# ── shared in-memory DB fixture ───────────────────────────────────────────────

@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ── Alert tests ───────────────────────────────────────────────────────────────

def test_create_alert(db):
    alert = AlertDB(
        threat_id="T1059",
        title="PowerShell Execution",
        description="Suspicious PS activity",
        priority="P2",
        status="open",
        indicators=["ps.exe", "cmd.exe"],
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    assert alert.id is not None
    assert alert.threat_id == "T1059"
    assert alert.priority == "P2"
    assert alert.status == "open"


def test_alert_default_status(db):
    alert = AlertDB(threat_id="T1078", title="Valid Accounts", description="Brute force detected")
    db.add(alert)
    db.commit()
    db.refresh(alert)
    assert alert.status == "open"


def test_alert_triggered_at_auto_set(db):
    alert = AlertDB(threat_id="T1078", title="Valid Accounts", description="Brute force detected")
    db.add(alert)
    db.commit()
    db.refresh(alert)
    assert alert.triggered_at is not None


def test_update_alert_status(db):
    alert = AlertDB(threat_id="T1021", title="Remote Services", description="Lateral movement")
    db.add(alert)
    db.commit()
    alert.status = "resolved"
    db.commit()
    db.refresh(alert)
    assert alert.status == "resolved"


def test_delete_alert(db):
    alert = AlertDB(threat_id="T1003", title="Credential Dump", description="LSASS access")
    db.add(alert)
    db.commit()
    alert_id = alert.id
    db.delete(alert)
    db.commit()
    result = db.query(AlertDB).filter(AlertDB.id == alert_id).first()
    assert result is None


def test_filter_alerts_by_status(db):
    db.add(AlertDB(threat_id="T1001", title="A", description="d", status="open"))
    db.add(AlertDB(threat_id="T1002", title="B", description="d", status="resolved"))
    db.add(AlertDB(threat_id="T1003", title="C", description="d", status="open"))
    db.commit()
    open_alerts = db.query(AlertDB).filter(AlertDB.status == "open").all()
    assert len(open_alerts) == 2


def test_alert_indicators_stored_as_json(db):
    alert = AlertDB(
        threat_id="T1059",
        title="PS Alert",
        description="test",
        indicators=["ioc1", "ioc2", "ioc3"],
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    assert alert.indicators == ["ioc1", "ioc2", "ioc3"]


# ── Playbook tests ────────────────────────────────────────────────────────────

def test_create_playbook(db):
    playbook = PlaybookDB(
        threat_id="T1059",
        title="IR Playbook: T1059",
        objective="Contain PowerShell abuse",
        steps=[{"step_number": 1, "action": "Isolate host"}],
        status="active",
        tags=["auto-generated", "T1059"],
        generated_by="CyberMind",
        version=1,
    )
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    assert playbook.id is not None
    assert playbook.threat_id == "T1059"
    assert playbook.version == 1


def test_playbook_steps_stored_as_json(db):
    steps = [
        {"step_number": 1, "action": "Isolate host", "responsible_team": "SOC Tier 2"},
        {"step_number": 2, "action": "Review SIEM logs", "responsible_team": "SOC Tier 1"},
    ]
    playbook = PlaybookDB(
        threat_id="T1078",
        title="IR Playbook: T1078",
        objective="Contain valid account abuse",
        steps=steps,
        generated_by="CyberMind",
        version=1,
    )
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    assert len(playbook.steps) == 2
    assert playbook.steps[0]["action"] == "Isolate host"


def test_playbook_default_status(db):
    playbook = PlaybookDB(
        threat_id="T1003",
        title="IR Playbook: T1003",
        objective="Contain credential dumping",
        generated_by="CyberMind",
        version=1,
    )
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    assert playbook.status == "draft"


def test_delete_playbook(db):
    playbook = PlaybookDB(
        threat_id="T1021",
        title="IR Playbook: T1021",
        objective="Contain lateral movement",
        generated_by="CyberMind",
        version=1,
    )
    db.add(playbook)
    db.commit()
    playbook_id = playbook.id
    db.delete(playbook)
    db.commit()
    result = db.query(PlaybookDB).filter(PlaybookDB.id == playbook_id).first()
    assert result is None


# ── Entity tests ──────────────────────────────────────────────────────────────

def test_create_entity(db):
    entity = EntityDB(
        entity_id="apt29",
        name="APT29",
        entity_type="threat_actor",
        description="Russian SVR-linked threat actor",
        source="MITRE ATT&CK",
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    assert entity.id is not None
    assert entity.entity_id == "apt29"
    assert entity.risk_score == 0.0


def test_entity_unique_entity_id(db):
    db.add(EntityDB(
        entity_id="apt28",
        name="APT28",
        entity_type="threat_actor",
        description="Russian GRU-linked threat actor",
    ))
    db.commit()
    duplicate = EntityDB(
        entity_id="apt28",
        name="APT28 Duplicate",
        entity_type="threat_actor",
        description="Duplicate",
    )
    db.add(duplicate)
    with pytest.raises(Exception):
        db.commit()


def test_entity_relationships_stored_as_json(db):
    entity = EntityDB(
        entity_id="apt30",
        name="APT30",
        entity_type="threat_actor",
        description="Southeast Asia threat actor",
        relationships=[{"source_entity_id": "apt30", "target_entity_id": "malware-1", "relationship_type": "uses"}],
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    assert len(entity.relationships) == 1
    assert entity.relationships[0]["relationship_type"] == "uses"


def test_filter_entities_by_type(db):
    db.add(EntityDB(entity_id="apt31", name="APT31", entity_type="threat_actor", description="d"))
    db.add(EntityDB(entity_id="mal-1", name="Mimikatz", entity_type="malware", description="d"))
    db.add(EntityDB(entity_id="mal-2", name="Cobalt Strike", entity_type="malware", description="d"))
    db.commit()
    malware = db.query(EntityDB).filter(EntityDB.entity_type == "malware").all()
    assert len(malware) == 2


def test_entity_default_risk_score(db):
    entity = EntityDB(
        entity_id="tool-1",
        name="PsExec",
        entity_type="tool",
        description="Lateral movement tool",
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    assert entity.risk_score == 0.0