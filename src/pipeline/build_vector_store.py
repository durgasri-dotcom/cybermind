from __future__ import annotations

import json
from pathlib import Path

from configs.logging_config import get_logger
from configs.settings import settings
from src.backend.services.rag_service import get_rag_service

logger = get_logger(__name__)


def load_gold(path: str | None = None) -> list[dict]:
    p = Path(path or settings.mitre_gold_path)
    if not p.exists():
        raise FileNotFoundError(f"Gold data not found at {p}. Run transform_threats.py first.")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def run() -> None:
    logger.info("vector_store_build_start")

    threats = load_gold()
    logger.info("gold_data_loaded", count=len(threats))

    documents = [
        {
            "threat_id": t["threat_id"],
            "text": t.get("text") or f"{t.get('name', '')}. {t.get('description', '')}",
            "source": t.get("source", "MITRE ATT&CK"),
            "metadata": {
                "name": t.get("name", ""),
                "category": t.get("category", ""),
                "severity": t.get("severity", "unknown"),
                "risk_score": t.get("risk_score", 0.0),
                "platforms": t.get("platforms", []),
            },
        }
        for t in threats
        if t.get("text") or t.get("description")
    ]

    logger.info("documents_prepared", count=len(documents))

    rag = get_rag_service()
    total_chunks = rag.build_index_from_documents(documents)

    logger.info("vector_store_build_complete", total_chunks=total_chunks)


if __name__ == "__main__":
    run()