from __future__ import annotations

from fastapi import APIRouter

from src.backend.services.ioc_service import get_ioc_service

router = APIRouter()


@router.get("/ioc/pulses")
async def get_recent_pulses(limit: int = 10):
    ioc_svc = get_ioc_service()
    pulses = ioc_svc.get_recent_pulses(limit=limit)
    return {
        "pulses": pulses,
        "total": len(pulses),
        "source": "AlienVault OTX",
    }


@router.get("/ioc/search")
async def search_ioc(q: str):
    ioc_svc = get_ioc_service()
    results = ioc_svc.search_ioc(query=q)
    return results