from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

import httpx

from configs.logging_config import get_logger

logger = get_logger(__name__)

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_REQUEST_DELAY = 6.0  


class CVEService:
    """Fetches, parses, and scores CVEs from the NVD API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.headers = {"apiKey": api_key} if api_key else {}
        
        self.delay = 0.6 if api_key else NVD_REQUEST_DELAY

    # ── public methods ────────────────────────────────────────────────────────

    def fetch_recent(self, days: int = 7, max_results: int = 20) -> list[dict]:
        """Fetch CVEs published in the last N days."""
        from datetime import timedelta
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        params = {
            "pubStartDate": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate": end.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "resultsPerPage": min(max_results, 2000),
        }
        return self._fetch_and_parse(params)

    def fetch_by_severity(self, severity: str, max_results: int = 20) -> list[dict]:
        """Fetch CVEs by CVSS severity: LOW, MEDIUM, HIGH, CRITICAL."""
        params = {
            "cvssV3Severity": severity.upper(),
            "resultsPerPage": min(max_results, 2000),
        }
        return self._fetch_and_parse(params)

    def fetch_by_keyword(self, keyword: str, max_results: int = 20) -> list[dict]:
        """Fetch CVEs matching a keyword (e.g. 'apache', 'windows', 'sql injection')."""
        params = {
            "keywordSearch": keyword,
            "resultsPerPage": min(max_results, 2000),
        }
        return self._fetch_and_parse(params)

    def fetch_by_id(self, cve_id: str) -> dict | None:
        """Fetch a single CVE by ID (e.g. 'CVE-2024-1234')."""
        params = {"cveId": cve_id}
        results = self._fetch_and_parse(params)
        return results[0] if results else None

    # ── internal ──────────────────────────────────────────────────────────────

    def _fetch_and_parse(self, params: dict) -> list[dict]:
        start = time.perf_counter()
        try:
            time.sleep(self.delay)
            with httpx.Client(timeout=30.0) as client:
                response = client.get(NVD_BASE_URL, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as e:
            logger.error("nvd_fetch_error", error=str(e), params=params)
            return []

        vulnerabilities = data.get("vulnerabilities", [])
        parsed = [self._parse_cve(v) for v in vulnerabilities]
        parsed = [p for p in parsed if p is not None]

        elapsed = (time.perf_counter() - start) * 1000
        logger.info("nvd_fetch_complete", count=len(parsed), latency_ms=round(elapsed, 2))
        return parsed

    def _parse_cve(self, vuln: dict) -> dict | None:
        try:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")
            if not cve_id:
                return None

            
            descriptions = cve.get("descriptions", [])
            description = next(
                (d["value"] for d in descriptions if d.get("lang") == "en"),
                "No description available",
            )

            
            cvss_score, cvss_severity, cvss_vector = self._extract_cvss(cve)

            
            published = self._parse_date(cve.get("published"))
            modified = self._parse_date(cve.get("lastModified"))

            
            cwe_ids = []
            for weakness in cve.get("weaknesses", []):
                for desc in weakness.get("description", []):
                    val = desc.get("value", "")
                    if val.startswith("CWE-"):
                        cwe_ids.append(val)

            # affected products (CPE)
            affected_products = []
            configs = cve.get("configurations", [])
            for config in configs[:1]:  
                for node in config.get("nodes", [])[:3]:
                    for cpe_match in node.get("cpeMatch", [])[:5]:
                        cpe = cpe_match.get("criteria", "")
                        if cpe:
                            affected_products.append(cpe)

            
            risk_score = self._compute_risk_score(cvss_score, cvss_severity, cwe_ids)

            return {
                "cve_id": cve_id,
                "description": description,
                "cvss_score": cvss_score,
                "cvss_severity": cvss_severity,
                "cvss_vector": cvss_vector,
                "published_date": published,
                "modified_date": modified,
                "cwe_ids": cwe_ids,
                "affected_products": affected_products,
                "mitre_techniques": self._map_to_mitre(cwe_ids, description),
                "risk_score": risk_score,
                "raw_nvd": cve,
            }
        except Exception as e:
            logger.warning("cve_parse_error", error=str(e))
            return None

    def _extract_cvss(self, cve: dict) -> tuple[float | None, str | None, str | None]:
        metrics = cve.get("metrics", {})
        # prefer v3.1, fallback to v3.0, then v2
        for key in ("cvssMetricV31", "cvssMetricV30"):
            entries = metrics.get(key, [])
            if entries:
                data = entries[0].get("cvssData", {})
                return (
                    data.get("baseScore"),
                    data.get("baseSeverity"),
                    data.get("vectorString"),
                )
        entries = metrics.get("cvssMetricV2", [])
        if entries:
            data = entries[0].get("cvssData", {})
            score = data.get("baseScore")
            severity = entries[0].get("baseSeverity")
            return score, severity, data.get("vectorString")
        return None, None, None

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _compute_risk_score(
        self,
        cvss_score: float | None,
        severity: str | None,
        cwe_ids: list[str],
    ) -> float:
        """Normalize CVSS + severity + CWE count into a 0-1 risk score."""
        score = 0.0
        if cvss_score is not None:
            score = cvss_score / 10.0
        elif severity:
            mapping = {"CRITICAL": 0.95, "HIGH": 0.75, "MEDIUM": 0.5, "LOW": 0.25}
            score = mapping.get(severity.upper(), 0.3)
        
        if len(cwe_ids) > 1:
            score = min(score + 0.05, 1.0)
        return round(score, 4)

    def _map_to_mitre(self, cwe_ids: list[str], description: str) -> list[str]:
        """Heuristic mapping from CWE/description keywords to MITRE techniques."""
        techniques = []
        desc_lower = description.lower()
        cwe_map = {
            "CWE-78":  "T1059",   
            "CWE-89":  "T1190",   
            "CWE-79":  "T1059.007",  
            "CWE-22":  "T1083",   
            "CWE-287": "T1078",   
            "CWE-306": "T1078",   
            "CWE-434": "T1105",   
            "CWE-502": "T1059",   
        }
        for cwe in cwe_ids:
            if cwe in cwe_map:
                t = cwe_map[cwe]
                if t not in techniques:
                    techniques.append(t)

        
        keyword_map = {
            "remote code execution": "T1059",
            "privilege escalation": "T1068",
            "credential": "T1078",
            "lateral movement": "T1021",
            "command injection": "T1059",
            "buffer overflow": "T1203",
            "denial of service": "T1499",
        }
        for keyword, technique in keyword_map.items():
            if keyword in desc_lower and technique not in techniques:
                techniques.append(technique)

        return techniques[:5] 


# ── singleton ─────────────────────────────────────────────────────────────────

_cve_service: CVEService | None = None


def get_cve_service() -> CVEService:
    global _cve_service
    if _cve_service is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("NVD_API_KEY")  
        _cve_service = CVEService(api_key=api_key)
    return _cve_service 