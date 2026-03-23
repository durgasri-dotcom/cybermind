from __future__ import annotations
from configs.settings import settings
from src.backend.models.threat import SeverityLevel


def compute_risk_score(
    base_score: float = 0.0,
    has_public_exploit: bool = False,
    is_actively_exploited: bool = False,
    affected_platforms: list[str] | None = None,
    mitigation_count: int = 0,
) -> float:
    score = base_score

    if has_public_exploit:
        score += 0.15

    if is_actively_exploited:
        score += 0.20

    platform_count = len(affected_platforms) if affected_platforms else 0
    if platform_count >= 3:
        score += 0.10
    elif platform_count >= 1:
        score += 0.05

    if mitigation_count == 0:
        score += 0.10
    elif mitigation_count <= 2:
        score += 0.05

    return round(min(score, 1.0), 4)


def score_to_severity(risk_score: float) -> SeverityLevel:
    if risk_score >= settings.risk_score_critical:
        return SeverityLevel.CRITICAL
    if risk_score >= settings.risk_score_high:
        return SeverityLevel.HIGH
    if risk_score >= settings.risk_score_medium:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def bulk_score(threats: list[dict]) -> list[dict]:
    for threat in threats:
        threat["risk_score"] = compute_risk_score(
            base_score=threat.get("base_score", 0.0),
            has_public_exploit=threat.get("has_public_exploit", False),
            is_actively_exploited=threat.get("is_actively_exploited", False),
            affected_platforms=threat.get("platforms", []),
            mitigation_count=len(threat.get("mitigations", [])),
        )
        threat["severity"] = score_to_severity(threat["risk_score"]).value
    return threats