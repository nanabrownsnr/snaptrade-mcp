"""Twynity JWT verification for Streamable HTTP requests."""

from fastmcp.server.auth.providers.jwt import JWTVerifier

from app.config import settings


def get_auth_provider() -> JWTVerifier:
    jwks_url = f"{settings.ACCOUNT_SERVICE_URL.rstrip('/')}/{settings.ACCOUNT_SERVICE_JWKS_ENDPOINT.lstrip('/')}"
    return JWTVerifier(jwks_uri=jwks_url)
