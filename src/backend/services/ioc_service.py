from __future__ import annotations

import httpx

from configs.logging_config import get_logger
from configs.settings import settings

logger = get_logger(__name__)

OTX_BASE = "https://otx.alienvault.com/api/v1"

MITRE_MAP = {
    "domain": "T1583.001",
    "hostname": "T1583.001",
    "IPv4": "T1071.001",
    "IPv6": "T1071.001",
    "URL": "T1071.001",
    "FileHash-MD5": "T1027",
    "FileHash-SHA1": "T1027",
    "FileHash-SHA256": "T1027",
    "email": "T1566.001",
    "CVE": "T1190",
}


class IOCService:
    def __init__(self) -> None:
        self._api_key = settings.otx_api_key
        self._headers = {"X-OTX-API-KEY": self._api_key}

    def get_recent_pulses(self, limit: int = 10) -> list[dict]:
        try:
            r = httpx.get(
                f"{OTX_BASE}/pulses/subscribed",
                headers=self._headers,
                params={"limit": limit},
                timeout=15,
            )
            r.raise_for_status()
            pulses = r.json().get("results", [])
            result = []
            for pulse in pulses:
                indicators = []
                for ioc in pulse.get("indicators", [])[:10]:
                    ioc_type = ioc.get("type", "unknown")
                    indicators.append({
                        "indicator": ioc.get("indicator", ""),
                        "type": ioc_type,
                        "mitre_technique": MITRE_MAP.get(ioc_type, "T1071"),
                        "description": ioc.get("description", ""),
                    })
                result.append({
                    "pulse_id": pulse.get("id", ""),
                    "name": pulse.get("name", ""),
                    "description": pulse.get("description", "")[:200],
                    "author": pulse.get("author_name", ""),
                    "tags": pulse.get("tags", [])[:5],
                    "indicator_count": pulse.get("indicator_count", 0),
                    "indicators": indicators,
                    "created": pulse.get("created", ""),
                    "tlp": pulse.get("tlp", "white"),
                })
            logger.info("otx_pulses_fetched", count=len(result))
            return result
        except Exception as e:
            logger.error("otx_fetch_failed", error=str(e))
            return []

    def search_ioc(self, query: str) -> dict:
        try:
            r = httpx.get(
                f"{OTX_BASE}/search/pulses",
                headers=self._headers,
                params={"q": query, "limit": 5},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error("otx_search_failed", error=str(e))
            return {}


def get_ioc_service() -> IOCService:
    return IOCService()