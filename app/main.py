"""Streamable HTTP, read-only SnapTrade MCP."""

import asyncio
from contextlib import asynccontextmanager, suppress

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware as MCPMiddleware
from fastmcp.server.middleware import MiddlewareContext
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth import get_auth_provider
from app.config import settings
from app.extended_tools import register_extended_tools
from app.license import license_watcher
from app.snaptrade import cash, holdings
from app.storage import get_connection, initialize, save_connection
from app.usage import save_usage_report


@asynccontextmanager
async def lifespan(server):
    initialize()
    task = asyncio.create_task(license_watcher())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


mcp = FastMCP(settings.APP_TITLE, auth=get_auth_provider(), lifespan=lifespan)


def owner_id() -> str:
    token = get_access_token()
    if token is None or not token.claims.get("id"):
        raise ValueError("Authenticated Twynity user is required")
    return str(token.claims["id"])


@mcp.tool
def get_portfolio_holdings() -> dict:
    """Return normalized, read-only holdings from all linked brokerage accounts.

    Call this when portfolio positions, quantities, prices, cost basis, or
    account types are needed. No trade or write operation is exposed.
    Example: ``get_portfolio_holdings()``.
    """
    return holdings(owner_id())


@mcp.tool
def get_cash_balances() -> dict:
    """Return uninvested cash balances across all linked accounts.

    Example: ``get_cash_balances()``. Returns account IDs, account types, and
    provider-reported currency balances without exposing credentials.
    """
    return cash(owner_id())


class UsageTrackingMiddleware(MCPMiddleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        await save_usage_report("TOOL_CALL", context.message.name, None)
        return await call_next(context)


mcp.add_middleware(UsageTrackingMiddleware())
register_extended_tools(mcp, owner_id)


@mcp.custom_route(f"{settings.API_V1_STR}/schema", methods=["GET"])
async def schema(request: Request) -> JSONResponse:
    return JSONResponse({"name": "snaptrade_connections", "endpoint": f"{settings.API_V1_STR}/snaptrade_connections", "method": "POST", "schema": {"client_id": "string", "consumer_key": "string"}})


@mcp.custom_route(f"{settings.API_V1_STR}/snaptrade_connections", methods=["POST"])
async def configure(request: Request) -> JSONResponse:
    user = owner_id()
    payload = await request.json()
    if not payload.get("client_id") or not payload.get("consumer_key"):
        return JSONResponse({"detail": "client_id and consumer_key are required"}, status_code=422)
    save_connection(user, payload["client_id"], payload["consumer_key"])
    return JSONResponse({"configured": True})


@mcp.custom_route(f"{settings.API_V1_STR}/external-connection/me", methods=["GET"])
async def connection_status(request: Request) -> JSONResponse:
    return JSONResponse({"connected": get_connection(owner_id()) is not None})


@mcp.custom_route(f"{settings.API_V1_STR}/.well-known/mcp.json", methods=["GET"])
async def manifest(request: Request) -> JSONResponse:
    return JSONResponse({"name": settings.APP_TITLE, "base_url": str(request.base_url).rstrip("/") + "/mcp", "version": settings.APP_VERSION, "external_connections": {"project": {"name": "snaptrade_connections"}, "api_key": None, "oauth": None}})


@mcp.custom_route(f"{settings.API_V1_STR}/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": settings.SERVICE_ID})


app = mcp.http_app()
