"""Streamable HTTP, read-only SnapTrade MCP."""

import asyncio
from contextlib import asynccontextmanager, suppress

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware as MCPMiddleware
from fastmcp.server.middleware import MiddlewareContext
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app.auth import get_auth_provider
from app.config import settings
from app.extended_tools import register_extended_tools
from app.license import license_watcher
from app.snaptrade import cash, holdings
from app.storage import initialize
from app.twynity import register_routes
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
register_routes(mcp)
register_extended_tools(mcp, owner_id)




origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()] or ["*"]
app = mcp.http_app(middleware=[Middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"], expose_headers=["mcp-session-id"])], transport="streamable-http", stateless_http=True, json_response=True)
