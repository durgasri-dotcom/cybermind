from __future__ import annotations

import time

from fastapi import Request
from sqlalchemy.orm import Session

from configs.logging_config import get_logger
from src.backend.database.engine import SessionLocal
from src.backend.database.db_models import RequestLogDB

logger = get_logger(__name__)

EXCLUDED_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}


async def request_logging_middleware(request: Request, call_next):
    if request.url.path in EXCLUDED_PATHS:
        return await call_next(request)

    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start) * 1000

    try:
        db: Session = SessionLocal()
        log = RequestLogDB(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(log)
        db.commit()
        db.close()
    except Exception as e:
        logger.warning("request_log_failed", error=str(e))

    return response