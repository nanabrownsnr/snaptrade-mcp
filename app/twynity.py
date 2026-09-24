"""Twynity manifest, connection, health, and schema routes."""

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth import get_current_user
from app.config import settings
from app.storage import get_connection, save_connection


def register_routes(mcp):
    @mcp.custom_route("/api/v1/schema", methods=["GET"])
    async def schema(request: Request):
        return JSONResponse({"name":"snaptrade_connections","endpoint":"/api/v1/snaptrade_connections","method":"POST","schema":{"client_id":"string","consumer_key":"string"}})
    @mcp.custom_route("/api/v1/snaptrade_connections", methods=["POST","OPTIONS"])
    async def configure(request: Request):
        if request.method == "OPTIONS": return JSONResponse({}, status_code=204)
        try: user=get_current_user()
        except ValueError: return JSONResponse({"detail":"Authentication required."}, status_code=401)
        payload=await request.json()
        if not payload.get("client_id") or not payload.get("consumer_key"):
            return JSONResponse({"detail":"client_id and consumer_key are required"}, status_code=422)
        save_connection(user["id"], payload["client_id"], payload["consumer_key"])
        return JSONResponse({"configured":True})
    @mcp.custom_route("/api/v1/external-connection/me", methods=["GET"])
    async def external_connection_me(request: Request):
        try: user=get_current_user()
        except ValueError: return JSONResponse({"detail":"Authentication required."}, status_code=401)
        return JSONResponse({"connected": get_connection(user["id"]) is not None})
    @mcp.custom_route("/api/v1/.well-known/mcp.json", methods=["GET"])
    async def manifest(request: Request):
        return JSONResponse({"name":settings.APP_TITLE,"base_url":f"{settings.PUBLIC_URL}/mcp","version":settings.APP_VERSION,"external_connections":{"project":{"name":"snaptrade_connections"}}})
    @mcp.custom_route("/api/v1/health", methods=["GET"])
    async def health(request: Request):
        return JSONResponse({"status":"ok","service":settings.SERVICE_ID})
