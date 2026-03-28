from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database.engine import Base
from src.backend.database import db_models  # noqa: F401
from src.backend.database.db_models import CveDB
from src.backend.services.cve_service import CVEService


# ── fixture ───────────────────────────────────────────────────────────────────

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


@pytest.fixture
def svc():
    return CVEService(api_key=None)


# ── CVEService unit tests (no network) ───────────────────────────────────────

def test_compute_risk_score_from_cvss():
    svc = CVEService()
    score = svc._compute_risk_score(8.5, "HIGH", [])
    assert score == 0.85


def test_compute_risk_score_from_severity_only():
    svc = CVEService()
    score = svc._compute_risk_score(None, "CRITICAL", [])
    assert score == 0.95


def test_compute_risk_score_medium():
    svc = CVEService()
    score = svc._compute_risk_score(None, "MEDIUM", [])
    assert score == 0.5


def test_compute_risk_score_capped_at_one():
    svc = CVEService()
    score = svc._compute_risk_score(9.9, "CRITICAL", ["CWE-79", "CWE-89"])
    assert score <= 1.0


def test_compute_risk_score_cwe_bonus():
    svc = CVEService()
    score_no_cwe = svc._compute_risk_score(5.0, "MEDIUM", [])
    score_with_cwe = svc._compute_risk_score(5.0, "MEDIUM", ["CWE-79", "CWE-89"])
    assert score_with_cwe > score_no_cwe


def test_map_to_mitre_cwe_injection():
    svc = CVEService()
    techniques = svc._map_to_mitre(["CWE-78"], "OS command injection vulnerability")
    assert "T1059" in techniques


def test_map_to_mitre_xss():
    svc = CVEService()
    techniques = svc._map_to_mitre(["CWE-79"], "Cross-site scripting vulnerability")
    assert "T1059.007" in techniques


def test_map_to_mitre_keyword_rce():
    svc = CVEService()
    techniques = svc._map_to_mitre([], "allows remote code execution on affected systems")
    assert "T1059" in techniques


def test_map_to_mitre_keyword_privesc():
    svc = CVEService()
    techniques = svc._map_to_mitre([], "leads to privilege escalation via crafted request")
    assert "T1068" in techniques


def test_map_to_mitre_capped_at_five():
    svc = CVEService()
    techniques = svc._map_to_mitre(
        ["CWE-78", "CWE-89", "CWE-79", "CWE-22", "CWE-287"],
        "remote code execution privilege escalation credential lateral movement",
    )
    assert len(techniques) <= 5


def test_parse_date_valid():
    svc = CVEService()
    dt = svc._parse_date("2024-01-15T10:30:00.000")
    assert dt is not None
    assert dt.year == 2024


def test_parse_date_none():
    svc = CVEService()
    dt = svc._parse_date(None)
    assert dt is None


def test_parse_date_invalid():
    svc = CVEService()
    dt = svc._parse_date("not-a-date")
    assert dt is None


# ── CveDB ORM tests ───────────────────────────────────────────────────────────

def test_create_cve(db):
    cve = CveDB(
        cve_id="CVE-2024-1234",
        description="Test vulnerability",
        cvss_score=7.5,
        cvss_severity="HIGH",
        risk_score=0.75,
        cwe_ids=["CWE-79"],
        mitre_techniques=["T1059.007"],
    )
    db.add(cve)
    db.commit()
    db.refresh(cve)
    assert cve.id is not None
    assert cve.cve_id == "CVE-2024-1234"
    assert cve.risk_score == 0.75


def test_cve_unique_constraint(db):
    db.add(CveDB(cve_id="CVE-2024-9999", description="First", risk_score=0.5))
    db.commit()
    db.add(CveDB(cve_id="CVE-2024-9999", description="Duplicate", risk_score=0.5))
    with pytest.raises(Exception):
        db.commit()


def test_cve_json_fields(db):
    cve = CveDB(
        cve_id="CVE-2024-5678",
        description="SQL injection",
        cvss_score=9.1,
        cvss_severity="CRITICAL",
        risk_score=0.91,
        cwe_ids=["CWE-89", "CWE-20"],
        mitre_techniques=["T1190", "T1059"],
        affected_products=["cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*"],
    )
    db.add(cve)
    db.commit()
    db.refresh(cve)
    assert len(cve.cwe_ids) == 2
    assert "T1190" in cve.mitre_techniques
    assert len(cve.affected_products) == 1


def test_filter_cves_by_severity(db):
    db.add(CveDB(cve_id="CVE-2024-0001", description="d", cvss_severity="CRITICAL", risk_score=0.95))
    db.add(CveDB(cve_id="CVE-2024-0002", description="d", cvss_severity="HIGH", risk_score=0.75))
    db.add(CveDB(cve_id="CVE-2024-0003", description="d", cvss_severity="CRITICAL", risk_score=0.90))
    db.commit()
    critical = db.query(CveDB).filter(CveDB.cvss_severity == "CRITICAL").all()
    assert len(critical) == 2


def test_cve_default_risk_score(db):
    cve = CveDB(cve_id="CVE-2024-0004", description="Low severity issue", risk_score=0.0)
    db.add(cve)
    db.commit()
    db.refresh(cve)
    assert cve.risk_score == 0.0