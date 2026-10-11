# backend/app/core/rate_limit.py

import os
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.security import decode_access_token

# Disable rate limiting during pytest test runs
is_testing = os.getenv("TESTING", "false").lower() == "true" or "pytest" in os.getenv("_", "")

def rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"
    return get_remote_address(request)

limiter = Limiter(key_func=rate_limit_key, enabled=not is_testing)