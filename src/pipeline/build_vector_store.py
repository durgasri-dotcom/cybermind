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


def load_cve_documents() -> list[dict]:
    """Load CVEs from SQLite and convert to RAG documents."""
    try:
        from src.backend.database.engine import SessionLocal, Base, engine
        from src.backend.database import db_models  # noqa: F401
        from src.backend.database.db_models import CveDB

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        cves = db.query(CveDB).all()
        db.close()

        documents = []
        for cve in cves:
            techniques = ", ".join(cve.mitre_techniques or []) or "unknown"
            cwes = ", ".join(cve.cwe_ids or []) or "unknown"
            text = (
                f"{cve.cve_id}: {cve.description} "
                f"Severity: {cve.cvss_severity or 'unknown'}. "
                f"CVSS Score: {cve.cvss_score or 0}. "
                f"CWE: {cwes}. "
                f"Related MITRE techniques: {techniques}."
            )
            documents.append({
                "threat_id": cve.cve_id,
                "text": text,
                "source": "NVD CVE",
                "metadata": {
                    "name": cve.cve_id,
                    "category": "CVE",
                    "severity": (cve.cvss_severity or "unknown").lower(),
                    "risk_score": cve.risk_score or 0.0,
                    "cvss_score": cve.cvss_score or 0.0,
                    "platforms": [],
                },
            })

        logger.info("cve_documents_loaded", count=len(documents))
        return documents

    except Exception as e:
        logger.warning("cve_documents_load_failed", error=str(e))
        return []


def run() -> None:
    logger.info("vector_store_build_start")

    # ── MITRE ATT&CK documents ────────────────────────────────────────────────
    threats = load_gold()
    logger.info("gold_data_loaded", count=len(threats))

    mitre_documents = [
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

    # ── CVE documents from SQLite ─────────────────────────────────────────────
    cve_documents = load_cve_documents()

    # ── combine and build index ───────────────────────────────────────────────
    all_documents = mitre_documents + cve_documents
    logger.info("documents_prepared",
                mitre=len(mitre_documents),
                cves=len(cve_documents),
                total=len(all_documents))

    rag = get_rag_service()
    total_chunks = rag.build_index_from_documents(all_documents)
    logger.info("vector_store_build_complete", total_chunks=total_chunks)


if __name__ == "__main__":
    run()