# src/hitl/tools.py
# Local LangGraph tools for the Human in the Loop agent.
#
# WHY THIS FILE EXISTS:
# buy_stock uses interrupt() which requires LangGraph context.
# It CANNOT be moved to an MCP server because interrupt() only works
# inside a tool that is part of the LangGraph graph.
# get_stock_price is handled by the MCP stock server instead.

from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def buy_stock(symbol: str, quantity: int, price: float) -> str:
    """
    Buy a given quantity of stock at the given price.
    Pauses execution using interrupt() and waits for human approval.

    Args:
        symbol   (str):   Stock ticker symbol. Example: "AAPL"
        quantity (int):   Number of shares to buy.
        price    (float): Price per share.

    Returns:
        str: Confirmation or cancellation message.
    """
    # interrupt() pauses the graph here and waits for human input.
    # The full graph state is saved to MemorySaver at this point.
    # Execution resumes only when Command(resume=decision) is passed back in.
    decision = interrupt(
        f"⏸️  Approve buying {quantity} shares of {symbol} at ${price} each?\n"
        f"    Total cost: ${round(quantity * price, 2)}\n"
        f"    Enter yes to approve or no to decline: "
    )

    if decision.strip().lower() == "yes":
        # Human approved — execute the trade.
        # Replace this with a real brokerage API call in production.
        return (
            f"✅ Successfully bought {quantity} shares of {symbol} "
            f"at ${price}. Total: ${round(quantity * price, 2)}"
        )
    else:
        # Human declined — cancel the trade.
        return f"❌ Purchase of {quantity} shares of {symbol} was cancelled."