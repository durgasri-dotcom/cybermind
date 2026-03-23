from __future__ import annotations
import json
from pathlib import Path
from configs.settings import settings
from configs.logging_config import get_logger

logger = get_logger(__name__)

TACTIC_MAP = {
    "TA0001": "Initial Access",
    "TA0002": "Execution",
    "TA0003": "Persistence",
    "TA0004": "Privilege Escalation",
    "TA0005": "Defense Evasion",
    "TA0006": "Credential Access",
    "TA0007": "Discovery",
    "TA0008": "Lateral Movement",
    "TA0009": "Collection",
    "TA0010": "Exfiltration",
    "TA0011": "Command and Control",
    "TA0040": "Impact",
}


def load_raw(path: str | None = None) -> dict:
    p = Path(path or settings.mitre_bronze_path)
    if not p.exists():
        raise FileNotFoundError(f"MITRE raw data not found at {p}. Run ingest_mitre.py first.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_techniques(raw: dict) -> list[dict]:
    techniques = []

    for obj in raw.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("x_mitre_deprecated", False) or obj.get("revoked", False):
            continue

        technique_id = _extract_technique_id(obj)
        if not technique_id:
            continue

        tactics = _extract_tactics(obj)
        platforms = obj.get("x_mitre_platforms", [])
        mitigations = []

        techniques.append({
            "threat_id": technique_id,
            "name": obj.get("name", ""),
            "description": obj.get("description", ""),
            "category": tactics[0] if tactics else "Unknown",
            "tags": tactics,
            "platforms": platforms,
            "mitigations": mitigations,
            "source": "MITRE ATT&CK",
            "base_score": _base_score(obj),
            "has_public_exploit": False,
            "is_actively_exploited": False,
            "text": f"{obj.get('name', '')}. {obj.get('description', '')}",
            "metadata": {
                "name": obj.get("name", ""),
                "tactics": tactics,
                "platforms": platforms,
            },
        })

    logger.info("mitre_techniques_parsed", count=len(techniques))
    return techniques


def save_normalized(techniques: list[dict], path: str | None = None) -> None:
    p = Path(path or settings.mitre_silver_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(techniques, f, indent=2)
    logger.info("mitre_normalized_saved", path=str(p), count=len(techniques))


def load_normalized(path: str | None = None) -> list[dict]:
    p = Path(path or settings.mitre_silver_path)
    if not p.exists():
        raise FileNotFoundError(f"Normalized data not found at {p}. Run transform_threats.py first.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_technique_id(obj: dict) -> str | None:
    for ref in obj.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id")
    return None


def _extract_tactics(obj: dict) -> list[str]:
    tactics = []
    for phase in obj.get("kill_chain_phases", []):
        if phase.get("kill_chain_name") == "mitre-attack":
            tactic_name = phase.get("phase_name", "").replace("-", " ").title()
            tactics.append(tactic_name)
    return tactics


def _base_score(obj: dict) -> float:
    detection = obj.get("x_mitre_detection", "")
    data_sources = obj.get("x_mitre_data_sources", [])
    score = 0.3
    if not detection:
        score += 0.1
    if len(data_sources) == 0:
        score += 0.1
    return round(min(score, 1.0), 4)