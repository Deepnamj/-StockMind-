# src/hitl/main.py
# Entry point for the Human in the Loop stock trading agent.
#
# Flow:
#   1. Connect to MCP stock server (get_stock_price)
#   2. Build LangGraph agent with MCP + local tools
#   3. Run interactive chat loop
#   4. Handle interrupt() for buy_stock approval
#
# Run from project root:
#   python -m src.hitl.main

import asyncio
import time

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.types import Command

from src.hitl.graph import build_hitl_graph

# Load GROQ_API_KEY from .env file
load_dotenv()


async def chat_loop():
    """
    Interactive HITL chat loop.

    Handles two cases:
      - Normal response: AI replies directly (e.g. get_stock_price)
      - Interrupted:     Graph pauses at buy_stock for human approval
    """
    # Connect to MCP stock server.
    # Uses stdio — launched automatically as a subprocess, no manual start needed.
    mcp_client = MultiServerMCPClient(
        {
            "stock": {
                "command": "python",
                "args": ["src/mcp_servers/stock_server.py"],
                "transport": "stdio",
            }
        }
    )

    # Build the agent graph.
    graph = await build_hitl_graph(mcp_client)

    # thread_id identifies this conversation in MemorySaver.
    # Same thread_id = same memory = graph resumes after interrupt.
    config = {"configurable": {"thread_id": "1"}}

    print("🤖 Stock Trading Assistant (type 'quit' to exit)\n")

    while True:
        user_input = input("You: ")

        # Exit condition.
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        # -- Step 1: Invoke graph with user message --------------------------
        # Using ainvoke (async) instead of invoke (sync) because MCP tools
        # are async — sync invoke causes "StructuredTool does not support
        # sync invocation" error.
        state = None
        for attempt in range(3):
            try:
                state = await graph.ainvoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config=config
                )
                break  # Success — exit retry loop.
            except Exception as e:
                if attempt < 2:
                    print(f"Connection failed, retrying... ({attempt + 1}/3)")
                    await asyncio.sleep(2)  # async sleep instead of time.sleep
                else:
                    print(f"Failed after 3 attempts: {str(e)}")

        # Skip if all retries failed.
        if state is None:
            print("Skipping — could not connect.")
            continue

        # -- Step 2: Check if graph paused at interrupt() --------------------
        # "__interrupt__" is set in state when interrupt() is hit
        # inside the buy_stock tool.
        interrupted = state.get("__interrupt__")

        if interrupted:
            # Show the approval prompt to the human.
            # interrupted[0].value is the message passed to interrupt().
            print(f"\n{interrupted[0].value}")

            # -- Step 3: Get human decision ----------------------------------
            decision = input("Your decision: ")

            # -- Step 4: Resume graph with human decision --------------------
            # Command(resume=decision) carries the decision back into the
            # exact line where interrupt() paused inside buy_stock.
            for attempt in range(3):
                try:
                    state = await graph.ainvoke(
                        Command(resume=decision),
                        config=config
                    )
                    print(f"\nAI: {state['messages'][-1].content}")
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"Connection failed, retrying... ({attempt + 1}/3)")
                        await asyncio.sleep(2)
                    else:
                        print(f"Failed after 3 attempts: {str(e)}")
        else:
            # No interrupt — AI responded directly.
            print(f"AI: {state['messages'][-1].content}")

        print("---")


def main():
    """
    Synchronous entry point — runs the async chat loop.
    """
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()