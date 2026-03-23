import pytest
from src.backend.services.threat_scoring import compute_risk_score, score_to_severity, bulk_score
from src.backend.models.threat import SeverityLevel


def test_compute_risk_score_base():
    score = compute_risk_score(base_score=0.3)
    assert 0.0 <= score <= 1.0


def test_compute_risk_score_with_exploit():
    score = compute_risk_score(base_score=0.3, has_public_exploit=True)
    assert score > 0.3


def test_compute_risk_score_actively_exploited():
    score = compute_risk_score(base_score=0.3, is_actively_exploited=True)
    assert score > 0.3


def test_compute_risk_score_capped_at_one():
    score = compute_risk_score(
        base_score=0.9,
        has_public_exploit=True,
        is_actively_exploited=True,
        affected_platforms=["Windows", "Linux", "macOS"],
        mitigation_count=0,
    )
    assert score <= 1.0


def test_score_to_severity_critical():
    assert score_to_severity(0.9) == SeverityLevel.CRITICAL


def test_score_to_severity_high():
    assert score_to_severity(0.7) == SeverityLevel.HIGH


def test_score_to_severity_medium():
    assert score_to_severity(0.5) == SeverityLevel.MEDIUM


def test_score_to_severity_low():
    assert score_to_severity(0.2) == SeverityLevel.LOW


def test_bulk_score():
    threats = [
        {"threat_id": "T1059", "base_score": 0.4, "platforms": ["Windows"], "mitigations": []},
        {"threat_id": "T1078", "base_score": 0.5, "has_public_exploit": True, "platforms": [], "mitigations": ["M1"]},
    ]
    result = bulk_score(threats)
    assert len(result) == 2
    for t in result:
        assert "risk_score" in t
        assert "severity" in t
        assert 0.0 <= t["risk_score"] <= 1.0