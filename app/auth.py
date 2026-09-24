"""Twynity JWT verification for Streamable HTTP requests."""

from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token

from app.config import settings


def get_auth_provider() -> JWTVerifier:
    jwks_url = f"{settings.ACCOUNT_SERVICE_URL.rstrip('/')}/{settings.ACCOUNT_SERVICE_JWKS_ENDPOINT.lstrip('/')}"
    return JWTVerifier(jwks_uri=jwks_url)


def get_current_user() -> dict:
    token = get_access_token()
    if token is None or not token.claims.get("id"):
        raise ValueError("Authenticated Twynity user is required")
    return {"id": str(token.claims["id"]), "email": token.claims.get("sub")}
