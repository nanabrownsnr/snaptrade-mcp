"""Read-only SnapTrade client operations and portfolio normalization."""

from typing import Any

from snaptrade_client import SnapTrade, SnapTradeAuth

from app.storage import get_connection


def _client(owner_id: str) -> tuple[SnapTrade, dict[str, str]]:
    connection = get_connection(owner_id)
    if connection is None:
        raise ValueError("SnapTrade is not configured for this user")
    return SnapTrade(
        auth=SnapTradeAuth.personal_api_key(
            consumer_key=connection["consumer_key"], client_id=connection["client_id"]
        )
    ), connection


def _body(response: Any) -> Any:
    return response.body if hasattr(response, "body") else response


def holdings(owner_id: str) -> dict:
    client, _ = _client(owner_id)
    accounts = _body(client.account_information.list_user_accounts())
    normalized = []
    for account in accounts or []:
        account_id = account.get("id") or account.get("brokerage_account_id")
        positions = _body(
            client.account_information.get_all_account_positions(account_id=account_id)
        )
        for position in positions or []:
            symbol = position.get("symbol", {})
            normalized.append(
                {
                    "ticker": symbol.get("symbol") if isinstance(symbol, dict) else symbol,
                    "security_type": position.get("security_type") or position.get("type"),
                    "quantity": position.get("units") or position.get("quantity"),
                    "current_price": position.get("price") or position.get("last_price"),
                    "cost_basis": position.get("average_purchase_price")
                    or position.get("cost_basis"),
                    "account_type": account.get("type") or account.get("account_type"),
                    "account_id": account_id,
                }
            )
    return {"holdings": normalized, "count": len(normalized)}


def cash(owner_id: str) -> dict:
    client, _ = _client(owner_id)
    accounts = _body(client.account_information.list_user_accounts())
    balances = []
    for account in accounts or []:
        account_id = account.get("id") or account.get("brokerage_account_id")
        balance = _body(client.account_information.get_user_account_balance(account_id=account_id))
        balances.append(
            {"account_id": account_id, "account_type": account.get("type"), "balances": balance}
        )
    return {"cash_balances": balances, "count": len(balances)}
