# src/hitl/graph.py
# Builds the LangGraph agent graph for the Human in the Loop stock trading agent.
#
# Combines:
#   - MCP tools  (get_stock_price) from stock_server.py via MultiServerMCPClient
#   - Local tool (buy_stock)       from tools.py with interrupt() for human approval

from langchain_core.messages import SystemMessage
#from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_groq import ChatGroq

from typing import Annotated
from typing_extensions import TypedDict

from src.hitl.tools import buy_stock  # Local tool with interrupt()


# ---------------------------------------------------------------------------
# State Definition
# ---------------------------------------------------------------------------

class State(TypedDict):
    """
    Holds the full conversation history.
    add_messages appends new messages instead of overwriting.
    """
    messages: Annotated[list, add_messages]


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

async def build_hitl_graph(mcp_client):
    """
    Builds and compiles the HITL LangGraph agent.

    Fetches get_stock_price from the MCP server and combines it with
    the local buy_stock tool that has interrupt() for human approval.

    Args:
        mcp_client: Connected MultiServerMCPClient instance.

    Returns:
        CompiledGraph: Ready-to-run graph with MemorySaver checkpointer.
    """
    # Fetch tools from the MCP stock server (get_stock_price).
    mcp_tools = await mcp_client.get_tools()

    # Combine MCP tools with local buy_stock tool.
    # buy_stock must stay local — interrupt() requires LangGraph context.
    all_tools = mcp_tools + [buy_stock]

    # Initialize Gemini LLM and bind all tools to it.
    llm = ChatGroq(model="llama-3.1-8b-instant")
   # llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    llm_with_tools = llm.bind_tools(all_tools)

    # -- Chatbot Node --------------------------------------------------------
    def chatbot(state: State):
        """
        Calls Gemini with the current conversation history.
        The LLM either responds directly or emits tool_calls.

        Args:
            state (State): Current graph state.

        Returns:
            dict: {"messages": [AIMessage]}
        """
        # System prompt defines the AI's behavior for the session.
        system = SystemMessage(content="""You are a helpful stock trading assistant.
        - Use get_stock_price tool to fetch current stock prices.
        - Use buy_stock tool when the user wants to buy shares.
        - Always confirm the total cost before buying.
        - For general questions, answer from your own knowledge.""")

        # Prepend system message to conversation history before calling LLM.
        return {"messages": [llm_with_tools.invoke([system] + state["messages"])]}

    # -- Graph Construction --------------------------------------------------
    builder = StateGraph(State)

    # Register nodes.
    builder.add_node("Chatbot", chatbot)           # LLM node
    builder.add_node("tools", ToolNode(all_tools)) # Tool execution node

    # Entry point — always start at Chatbot.
    builder.add_edge(START, "Chatbot")

    # After Chatbot: route to tools if tool_calls present, else END.
    builder.add_conditional_edges("Chatbot", tools_condition)

    # After tools finish: return to Chatbot to summarize results.
    builder.add_edge("tools", "Chatbot")

    # MemorySaver is REQUIRED for interrupt() to save and resume graph state.
    # Without it the graph cannot resume after an interrupt.
    memory = MemorySaver()

    return builder.compile(checkpointer=memory)