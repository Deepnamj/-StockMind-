# 🤖 StockMind — AI Stock Trading Assistant with Human Oversight

An AI-powered stock trading assistant built with **LangGraph**, **Groq (LLaMA)**, and **MCP (Model Context Protocol)** that fetches real-time stock prices and executes trades only after human approval.

---

## 📌 What It Does

- 📈 **Fetch real-time stock prices** — "What is Apple's stock price?"
- 💰 **Buy stocks with human approval** — AI pauses and waits for you to approve or decline before executing any trade
- 🔁 **ReAct reasoning loop** — AI decides which tool to call, calls it, reads the result, and responds
- 🛡️ **Human in the Loop (HITL)** — critical trade actions require human confirmation before proceeding

---

## 🏗️ Architecture
<img width="896" height="646" alt="image" src="https://github.com/user-attachments/assets/1330a9e4-8009-4cf1-a204-1fc387939d99" />



| Component | File | Role |
|---|---|---|
| Chat loop | `src/hitl/main.py` | Reads user input, calls `ainvoke`, handles `interrupt` |
| Agent graph | `src/hitl/graph.py` | LangGraph `StateGraph` with `MemorySaver` |
| LLM | Groq LLaMA 3.1 | Reasons and decides which tool to call |
| MCP tool | `src/mcp_servers/stock_server.py` | Fetches live stock price via Yahoo Finance |
| HITL tool | `src/hitl/tools.py` | Executes trade only after human approval via `interrupt()` |

---

## 📂 Project Structure

```
StockMind/
├── src/
│   ├── mcp_servers/
│   │   └── stock_server.py      # Real-time stock price MCP tool
│   │
│   ├── hitl/
│   │   ├── tools.py             # buy_stock tool with interrupt()
│   │   ├── graph.py             # LangGraph HITL agent
│   │   └── main.py              # Chat loop entry point
│   │
│   └── common.py                # LLM setup
│
├── .env                         # GROQ_API_KEY (never commit)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| [Groq + LLaMA 3.1](https://console.groq.com) | Fast LLM with tool calling |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Agent reasoning loop + HITL |
| [LangChain](https://www.langchain.com/) | LLM integration layer |
| [MCP (FastMCP)](https://github.com/jlowin/fastmcp) | Tool server protocol |
| [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) | Bridges MCP tools into LangChain |
| [httpx](https://www.python-httpx.org/) | Async HTTP requests |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Environment variable management |

---

## ⚙️ Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/StockMind.git
cd StockMind
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file
```
GROQ_API_KEY=your_groq_api_key_here
```

Get your free Groq API key at 👉 https://console.groq.com

### 4. Run
```bash
python -m src.hitl.main
```

---

## 💬 Example Usage

```
🤖 Stock Trading Assistant (type 'quit' to exit)

You: What is Apple's stock price?
AI: 📈 Apple Inc. (AAPL)
    Price:       189.45 USD
    Change:      ▲ 2.31 (1.23%)
    Prev Close:  187.14 USD
    Market:      REGULAR
---

You: Buy 10 shares of AAPL at 189.45

⏸️  Approve buying 10 shares of AAPL at $189.45 each?
    Total cost: $1894.5
    Enter yes to approve or no to decline:
Your decision: yes

AI: ✅ Successfully bought 10 shares of AAPL at $189.45. Total: $1894.50
---

You: Buy 5 shares of TSLA at 245.80

⏸️  Approve buying 5 shares of TSLA at $245.80 each?
    Total cost: $1229.0
    Enter yes to approve or no to decline:
Your decision: no

AI: ❌ Purchase of 5 shares of TSLA was cancelled.
---

You: quit
Goodbye!
```

---

## 🔧 MCP Server

### Stock Server (`stock_server.py`)
- **Tool:** `get_stock_price(symbol)`
- **API:** Yahoo Finance public API — free, no key needed
- **Transport:** stdio (auto-launched as subprocess — no manual startup needed)
- **Supports:** US stocks (`AAPL`, `TSLA`, `GOOGL`) and Indian stocks (`TCS.NS`, `INFY.NS`)

---

## 🧠 How Human in the Loop Works

```
User: "Buy 10 shares of AAPL at $189.45"
            ↓
Chatbot calls buy_stock tool
            ↓
⏸️ interrupt() — graph pauses, state saved to MemorySaver
            ↓
Human sees approval prompt and enters yes/no
            ↓
Command(resume=decision) — graph resumes at exact pause point
            ↓
yes → trade executed ✅
no  → trade cancelled ❌
            ↓
Chatbot summarizes result → END
```

### Key components

| Component | Role |
|---|---|
| `interrupt()` | Pauses graph inside `buy_stock` and waits for human input |
| `MemorySaver` | Saves graph state at pause point so it can be resumed |
| `thread_id` | Identifies the conversation to resume |
| `Command(resume=)` | Carries human decision back into the paused spot |

---

## 🔑 Why Two Types of Tools?

| Tool | Type | Why |
|---|---|---|
| `get_stock_price` | MCP server | Pure API call — no graph state needed, reusable across projects |
| `buy_stock` | Local `@tool` | Uses `interrupt()` which requires LangGraph context — cannot run in a separate process |

---

## 🚫 Common Errors

| Error | Fix |
|---|---|
| `API key required` | Add `GROQ_API_KEY` to `.env` file |
| `StructuredTool does not support sync invocation` | Use `await graph.ainvoke()` instead of `graph.invoke()` |
| `coroutine was never awaited` | Add `await` before `client.get_tools()` in `graph.py` |
| `ModuleNotFoundError: No module named 'src'` | Run with `python -m src.hitl.main` not `python src/hitl/main.py` |
| `429 RESOURCE_EXHAUSTED` | Free tier quota hit — wait 1 min or switch model |

---

## requirements.txt

```
langchain-groq
langgraph
langchain-mcp-adapters
langchain-core
httpx
python-dotenv
mcp
```

---

## 📄 License

MIT License — free to use and modify.

---

## 🙌 Acknowledgements

- [LangChain](https://www.langchain.com/) for the LLM tooling ecosystem
- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework and HITL support
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server library
- [Groq](https://console.groq.com) for the fast LLaMA inference
- [Yahoo Finance](https://finance.yahoo.com) for the free stock price API
