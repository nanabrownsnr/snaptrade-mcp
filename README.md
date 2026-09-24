# SnapTrade MCP

Read-only brokerage account access through SnapTrade using Streamable HTTP and Twynity JWT authentication.

This MCP exposes no trade execution, account deletion, or brokerage write tools.

## Tools

- `get_portfolio_holdings()` — normalized ticker, security type, quantity, price, cost basis, account type, and account ID.
- `get_cash_balances()` — cash balances across linked accounts.
- `list_accounts()` — linked brokerage accounts.
- `get_orders(account_id, status="all")` — read-only order history.
- `get_activities(account_id)` — dividends, fees, deposits, and transactions.
- `get_portfolio_summary()` — accounts, balances, and positions together.
- `search_symbols(query)` — search securities by ticker or name.
- `list_supported_brokerages()` — supported brokerage institutions.
- `check_snaptrade_status()` — SnapTrade connectivity and account count.
- `get_connection_portal_url()` — brokerage connection URL.

## SnapTrade authentication

This service uses SnapTrade Personal API Key authentication. Configure the two SnapTrade application values through the Twynity project connection flow:

```json
{
  "client_id": "your-personal-client-id",
  "consumer_key": "your-personal-consumer-key"
}
```

Personal mode does not use `userId` or `userSecret` on account-data calls.

## Twynity endpoints

- `GET /api/v1/schema`
- `POST /api/v1/snaptrade_connections`
- `GET /api/v1/external-connection/me`
- `GET /api/v1/.well-known/mcp.json`
- `GET /api/v1/health`
- MCP transport: `/mcp`

## Environment

Required:

- `ACCOUNT_SERVICE_URL`
- `ACCOUNT_SERVICE_JWKS_ENDPOINT`
- `ENCRYPTION_KEY` — a real Fernet key generated with `Fernet.generate_key()`
- `DATABASE_URL` — PostgreSQL connection URL, such as the Render external database URL

Optional Twynity settings include `USAGE_REPORT_ENDPOINT` and license service variables.

## Run

```bash
uv sync
export ACCOUNT_SERVICE_URL="..."
export ACCOUNT_SERVICE_JWKS_ENDPOINT="/.well-known/jwks.json"
export ENCRYPTION_KEY="..."
export DATABASE_URL="postgresql://..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t snaptrade-mcp:local .
docker run --rm -p 8002:8000 --env-file .env snaptrade-mcp:local
```

The service does not include a UI. The project structure remains open for adding MCP App resources later.
