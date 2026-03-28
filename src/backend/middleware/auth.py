from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(_API_KEY_HEADER)):
    expected = os.getenv("CYBERMIND_API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key