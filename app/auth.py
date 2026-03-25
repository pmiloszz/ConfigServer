from fastapi import Header, HTTPException, status

from app.settings import settings


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """
    FastAPI dependency for optional API key auth.

    - If settings.api_key is empty, auth is disabled and requests pass through.
    - If set, requests must include the matching X-API-Key header.
    """

    if not getattr(settings, "api_key", ""):
        return

    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
