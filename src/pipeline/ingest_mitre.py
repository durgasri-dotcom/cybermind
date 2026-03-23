from __future__ import annotations
import json
import httpx
from pathlib import Path
from configs.settings import settings
from configs.logging_config import get_logger

logger = get_logger(__name__)


def fetch_mitre_attack() -> dict:
    logger.info("fetching_mitre_attack", url=settings.mitre_attack_url)
    with httpx.Client(timeout=60.0) as client:
        response = client.get(settings.mitre_attack_url)
        response.raise_for_status()
    data = response.json()
    logger.info("mitre_attack_fetched", num_objects=len(data.get("objects", [])))
    return data


def save_raw(data: dict) -> None:
    p = Path(settings.mitre_bronze_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("mitre_raw_saved", path=str(p))


def run() -> None:
    data = fetch_mitre_attack()
    save_raw(data)
    logger.info("mitre_ingest_complete", total_objects=len(data.get("objects", [])))


if __name__ == "__main__":
    run()