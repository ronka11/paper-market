import json
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
import operator

from app.config import settings


llm = ChatOpenAI(
    model="openrouter/free",
    openai_api_key=settings.OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.3,
)


@tool
async def get_price_history(ticker: str, exchange: str = "US") -> str:
    """Get recent price history and calculate 7 day trend for a ticker."""
    import asyncio
    from app.database import AsyncSessionLocal
    from app.services.market import get_stored_history

    async with AsyncSessionLocal() as db:
        records = await get_stored_history(ticker, exchange, db)
        if not records:
            return json.dumps({"error": "No price data found"})

        recent = records[-7:]
        closes = [float(r.close) for r in recent]
        latest = closes[-1]
        week_ago = closes[0]
        trend_pct = ((latest - week_ago) / week_ago) * 100

        return json.dumps({
            "ticker": ticker,
            "latest_close": latest,
            "week_ago_close": week_ago,
            "trend_7d_pct": round(trend_pct, 2),
            "direction": "up" if trend_pct > 0 else "down",
        })

    # return json.dumps(asyncio.get_event_loop().run_until_complete(_run()))
    # return json.dumps(asyncio.run(_run()))


@tool
async def get_sentiment(ticker: str) -> str:
    """Get Reddit sentiment summary for a ticker."""
    import asyncio
    from app.database import AsyncSessionLocal
    from app.services.sentiment import get_sentiment_summary

    async with AsyncSessionLocal() as db:
        result = await get_sentiment_summary(ticker, db)

    # result = asyncio.get_event_loop().run_until_complete(_run())
    # result = asyncio.run(_run())
    return json.dumps(result)


@tool
async def get_portfolio_context(session_key: str) -> str:
    """Get current portfolio positions for context."""
    import asyncio
    from app.database import AsyncSessionLocal
    from app.services.portfolio import get_or_create_portfolio, get_positions

    async with AsyncSessionLocal() as db:
        portfolio = await get_or_create_portfolio(session_key, db)
        positions = await get_positions(portfolio.id, db)
        result = {
            "cash_balance": float(portfolio.cash_balance),
            "positions": [
                {"ticker": p.ticker, "quantity": p.quantity, "avg_cost": float(p.avg_cost)}
                for p in positions
            ]
        }

    # return json.dumps(asyncio.get_event_loop().run_until_complete(_run()))
    return json.dumps(result)



class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    ticker: str
    exchange: str
    session_key: str



tools = [get_price_history, get_sentiment, get_portfolio_context]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)


async def analyst_node(state: AgentState):
    from langchain_core.messages import HumanMessage, SystemMessage

    system = SystemMessage(content="""You are a financial analyst assistant for a paper trading app.
You have access to price history, sentiment data, and portfolio context tools.
When analysing a stock:
1. Always fetch price history first
2. Fetch sentiment if available
3. Fetch portfolio context to personalise advice
4. Return a structured JSON analysis with these exact keys:
   - ticker, exchange, latest_price, trend_7d_pct, trend_direction
   - sentiment_signal (bullish/bearish/neutral/unavailable)
   - stance (bull/bear/neutral)
   - summary (3-4 sentences max, plain English)
   - confidence (low/medium/high)
Return ONLY the JSON object, no markdown, no extra text.""")

    messages = [system] + state["messages"]
    # response = llm_with_tools.invoke(messages)
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


graph = StateGraph(AgentState)
graph.add_node("analyst", analyst_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("analyst")
graph.add_conditional_edges("analyst", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "analyst")

analyst_graph = graph.compile()



async def run_analysis(ticker: str, exchange: str, session_key: str) -> dict:
    from langchain_core.messages import HumanMessage

    result = await analyst_graph.ainvoke({
        "messages": [HumanMessage(content=f"Analyse {ticker} on {exchange} exchange for session {session_key}")],
        "ticker": ticker,
        "exchange": exchange,
        "session_key": session_key,
    })

    last_message = result["messages"][-1].content
    try:
        return json.loads(last_message)
    except json.JSONDecodeError:    
        # LLM didn't return clean JSON, return as-is
        return {"raw": last_message, "error": "parse_failed"}