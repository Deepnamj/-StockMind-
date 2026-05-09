# src/mcp_servers/stock_server.py
# An MCP server that exposes a single stock price lookup tool.
# Uses Yahoo Finance's public API — no API key required.
#
# Transport: stdio (auto-launched as subprocess by MultiServerMCPClient)
#
# Dependencies:
#   pip install httpx mcp

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

# Create the MCP server instance named "Stock".
mcp = FastMCP("Stock")


# ---------------------------------------------------------------------------
# Tool: Stock Price Fetcher
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_stock_price(symbol: str) -> str:
    """
    Get the current stock price for a given ticker symbol.

    Uses Yahoo Finance's public chart API — no API key needed.

    Args:
        symbol (str): The stock ticker symbol.
                      US stocks:     "AAPL", "TSLA", "GOOGL", "MSFT"
                      Indian stocks: "TCS.NS", "INFY.NS", "RELIANCE.NS"

    Returns:
        str: Formatted string with stock name, current price, change from
             previous close, and market state. Or an error message if the
             symbol is not found.

    Example prompts the agent understands:
        "What is Apple's stock price?"
        "Get the current price of Tesla"
        "How much is INFY.NS trading at?"
        "What is the stock price of GOOGL?"
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}",
                # User-Agent is required — Yahoo Finance blocks default httpx agents.
                headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            data = resp.json()

        # Navigate the nested Yahoo Finance response structure.
        result = data.get("chart", {}).get("result")

        if not result:
            error_msg = data.get("chart", {}).get("error", {})
            return (
                f"❌ No data found for symbol '{symbol.upper()}'. "
                f"Please check the ticker. {error_msg.get('description', '')}"
            )

        meta = result[0]["meta"]

        # Extract key fields from the meta object.
        price        = meta.get("regularMarketPrice", "N/A")
        currency     = meta.get("currency", "N/A")
        market_state = meta.get("marketState", "N/A")  # REGULAR, PRE, POST, CLOSED
        full_name    = meta.get("longName") or meta.get("shortName", symbol.upper())
        prev_close   = meta.get("previousClose", None)

        # Calculate price change from previous close if available.
        if prev_close and price != "N/A":
            change     = price - prev_close
            change_pct = (change / prev_close) * 100
            change_str = f"{'▲' if change >= 0 else '▼'} {abs(change):.2f} ({abs(change_pct):.2f}%)"
        else:
            change_str = "N/A"

        return (
            f"📈 {full_name} ({symbol.upper()})\n"
            f"   Price:       {price} {currency}\n"
            f"   Change:      {change_str}\n"
            f"   Prev Close:  {prev_close} {currency}\n"
            f"   Market:      {market_state}"
        )

    except httpx.TimeoutException:
        return "❌ Request timed out. Please try again."
    except httpx.HTTPStatusError as e:
        return f"❌ HTTP error {e.response.status_code} fetching data for '{symbol.upper()}'."
    except Exception as e:
        return f"❌ Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")