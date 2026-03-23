from __future__ import annotations
import json
from pathlib import Path
from configs.settings import settings
from configs.logging_config import get_logger
from src.backend.services.mitre_loader import load_normalized as load_mitre
from src.backend.services.threat_scoring import bulk_score

logger = get_logger(__name__)


def load_cve_normalized() -> list[dict]:
    p = Path(settings.cve_silver_path)
    if not p.exists():
        logger.warning("cve_normalized_not_found", path=str(p))
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def deduplicate(threats: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for t in threats:
        tid = t.get("threat_id", "")
        if tid and tid not in seen:
            seen.add(tid)
            unique.append(t)
    return unique


def clean_text(text: str) -> str:
    import re
    text = re.sub(r"\(Citation:.*?\)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def transform(threats: list[dict]) -> list[dict]:
    for t in threats:
        t["description"] = clean_text(t.get("description", ""))
        t["text"] = clean_text(t.get("text", ""))
        if not t.get("name"):
            t["name"] = t.get("threat_id", "Unknown")
    return threats


def save_gold(threats: list[dict]) -> None:
    p = Path(settings.mitre_gold_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(threats, f, indent=2)
    logger.info("gold_saved", path=str(p), count=len(threats))


def run() -> None:
    mitre = load_mitre()
    cves = load_cve_normalized()

    combined = mitre + cves
    logger.info("threats_combined", mitre=len(mitre), cve=len(cves), total=len(combined))

    deduped = deduplicate(combined)
    logger.info("threats_deduplicated", before=len(combined), after=len(deduped))

    transformed = transform(deduped)
    scored = bulk_score(transformed)

    save_gold(scored)
    logger.info("transform_complete", total=len(scored))


if __name__ == "__main__":
    run()