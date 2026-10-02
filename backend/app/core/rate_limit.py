# backend/app/core/rate_limit.py
#
# Rate limiting keyed by authenticated user, not IP. We decode the JWT
# ourselves here because slowapi's key_func only receives the raw Request
# — FastAPI's Depends() dependencies haven't run yet at this point.

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.security import decode_access_token


def rate_limit_key(request: Request) -> str:
    """
    Key by user id when there's a valid bearer token, otherwise fall back
    to client IP. Requests with no/invalid token will be rejected by
    get_current_user anyway — this fallback just avoids crashing here.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"
    return get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key)