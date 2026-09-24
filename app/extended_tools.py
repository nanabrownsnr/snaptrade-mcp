"""Additional read-only SnapTrade tools."""
from app.snaptrade import _body, _client


def register_extended_tools(mcp, owner_id):
    @mcp.tool
    def list_accounts() -> dict:
        """List all linked brokerage accounts. Example: list_accounts()."""
        c,_=_client(owner_id())
        data=_body(c.account_information.list_user_accounts()) or []
        return {"accounts":data,"count":len(data)}
    @mcp.tool
    def get_orders(account_id: str, status: str="all") -> dict:
        """Return read-only order history. Example: get_orders("account-id")."""
        c,_=_client(owner_id())
        args={"account_id":account_id}
        if status != "all":
            args["state"] = status
        return {"account_id":account_id,"orders":_body(c.account_information.get_user_account_orders(**args))}
    @mcp.tool
    def get_activities(account_id: str) -> dict:
        """Return dividends, fees, deposits, and transactions."""
        c,_=_client(owner_id())
        return {"account_id":account_id,"activities":_body(c.account_information.get_account_activities(account_id=account_id))}
    @mcp.tool
    def get_portfolio_summary() -> dict:
        """Return accounts, balances, and positions together."""
        c,_=_client(owner_id())
        out=[]
        for a in (_body(c.account_information.list_user_accounts()) or []):
            aid=a.get("id") or a.get("brokerage_account_id")
            out.append({"account":a,"balances":_body(c.account_information.get_user_account_balance(account_id=aid)),"positions":_body(c.account_information.get_all_account_positions(account_id=aid))})
        return {"portfolio":out,"account_count":len(out)}
    @mcp.tool
    def search_symbols(query: str) -> dict:
        """Search securities by ticker or name. Example: search_symbols("Apple")."""
        c,_=_client(owner_id())
        return {"query":query,"results":_body(c.reference_data.symbol_search_user_account(body={"substring":query}))}
    @mcp.tool
    def list_supported_brokerages() -> dict:
        """List supported brokerage institutions."""
        c,_=_client(owner_id())
        data=_body(c.reference_data.list_all_brokerages()) or []
        return {"brokerages":data,"count":len(data)}
    @mcp.tool
    def check_snaptrade_status() -> dict:
        """Check SnapTrade connectivity and account count."""
        c,_=_client(owner_id())
        data=_body(c.account_information.list_user_accounts()) or []
        return {"api":"connected","credentials":"configured","accounts":len(data)}
    @mcp.tool
    def get_connection_portal_url() -> dict:
        """Generate a brokerage connection URL."""
        c,_=_client(owner_id())
        data=_body(c.authentication.login_snap_trade_user())
        return {"redirect_uri":data.get("redirectURI")}
