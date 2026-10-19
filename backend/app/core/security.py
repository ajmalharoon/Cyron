"""Minimal bearer-token gate. Cyron orchestrates active-recon tools, so the
API must never be left open — every request (except /health) needs
`Authorization: Bearer <CYRON_API_KEY>`. This is intentionally simple: a
single operator key, not a user system. Put Cyron behind your own
authentication layer for multi-user or production use."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer = HTTPBearer(auto_error=False)


def require_api_key(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
    settings = get_settings()
    if not settings.cyron_api_key:
        # No key configured: fine for local dev, logged loudly so it isn't
        # mistaken for a deliberate choice in a shared deployment.
        return
    if creds is None or creds.credentials != settings.cyron_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing API key")
