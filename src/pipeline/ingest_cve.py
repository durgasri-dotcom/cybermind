from __future__ import annotations
import json
import time
import httpx
from pathlib import Path
from configs.settings import settings
from configs.logging_config import get_logger

logger = get_logger(__name__)

RESULTS_PER_PAGE = 2000
MAX_PAGES = 5


def fetch_recent_cves(days_back: int = 30) -> list[dict]:
    from datetime import datetime, timedelta, timezone

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)

    pub_start = start.strftime("%Y-%m-%dT%H:%M:%S.000")
    pub_end = end.strftime("%Y-%m-%dT%H:%M:%S.000")

    all_cves = []
    start_index = 0

    with httpx.Client(timeout=30.0) as client:
        for _ in range(MAX_PAGES):
            params = {
                "pubStartDate": pub_start,
                "pubEndDate": pub_end,
                "resultsPerPage": RESULTS_PER_PAGE,
                "startIndex": start_index,
            }
            response = client.get(settings.nvd_cve_url, params=params)
            response.raise_for_status()
            data = response.json()

            vulnerabilities = data.get("vulnerabilities", [])
            all_cves.extend(vulnerabilities)

            total = data.get("totalResults", 0)
            start_index += RESULTS_PER_PAGE

            logger.info("cve_page_fetched", fetched=len(all_cves), total=total)

            if start_index >= total:
                break

            time.sleep(0.6)

    return all_cves


def normalize_cves(raw_cves: list[dict]) -> list[dict]:
    normalized = []

    for item in raw_cves:
        cve = item.get("cve", {})
        cve_id = cve.get("id", "")
        if not cve_id:
            continue

        descriptions = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            "No description available",
        )

        metrics = cve.get("metrics", {})
        cvss_score = _extract_cvss_score(metrics)

        normalized.append({
            "threat_id": cve_id,
            "name": cve_id,
            "description": description,
            "category": "CVE",
            "source": "NVD",
            "base_score": cvss_score / 10.0 if cvss_score else 0.3,
            "platforms": [],
            "tags": ["CVE"],
            "mitigations": [],
            "text": f"{cve_id}. {description}",
            "metadata": {"name": cve_id, "cvss_score": cvss_score},
        })

    return normalized


def save_raw(data: list[dict]) -> None:
    p = Path(settings.cve_bronze_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("cve_raw_saved", path=str(p), count=len(data))


def save_normalized(data: list[dict]) -> None:
    p = Path(settings.cve_silver_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("cve_normalized_saved", path=str(p), count=len(data))


def _extract_cvss_score(metrics: dict) -> float | None:
    for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
        entries = metrics.get(version, [])
        if entries:
            return entries[0].get("cvssData", {}).get("baseScore")
    return None


def run(days_back: int = 30) -> None:
    raw = fetch_recent_cves(days_back=days_back)
    save_raw(raw)
    normalized = normalize_cves(raw)
    save_normalized(normalized)
    logger.info("cve_ingest_complete", total=len(normalized))


if __name__ == "__main__":
    run()