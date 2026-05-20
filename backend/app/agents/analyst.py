import json
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
import operator

from app.config import settings
from app.config import log


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

        price_history_res = json.dumps({
            "ticker": ticker,
            "latest_close": latest,
            "week_ago_close": week_ago,
            "trend_7d_pct": round(trend_pct, 2),
            "direction": "up" if trend_pct > 0 else "down",
        })
        log.info(f"get_price_history:  {price_history_res}")
        return price_history_res

    # return json.dumps(asyncio.get_event_loop().run_until_complete(_run()))
    # return json.dumps(asyncio.run(_run()))


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
    log.info(f"get_portfolio_context: {json.dumps(result)}")
    return json.dumps(result)

@tool
async def get_ticker_news_tool(ticker: str, exchange: str = "US") -> str:
    """Fetch recent news for a ticker to inform analysis."""
    from app.services.news import get_ticker_news

    normalized_ticker = ticker.upper().strip()

    if exchange.upper() == "NSE" and not normalized_ticker.endswith(".NS"):
        normalized_ticker = f"{normalized_ticker}.NS"
    elif exchange.upper() == "BSE" and not normalized_ticker.endswith(".BO"):
        normalized_ticker = f"{normalized_ticker}.BO"

    try:
        results = await get_ticker_news(normalized_ticker)

        if not results:
            return json.dumps({
                "ticker": normalized_ticker,
                "articles": [],
                "summary": "No recent news found"
            })

        return json.dumps(results)

    except Exception as e:
        log.exception(f"get_ticker_news_tool failed for {normalized_ticker}: {e}")

        return json.dumps({
            "ticker": normalized_ticker,
            "error": str(e),
            "articles": []
        })




class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    ticker: str
    exchange: str
    session_key: str



tools = [get_price_history, get_portfolio_context, get_ticker_news_tool]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)


async def analyst_node(state: AgentState):
    from langchain_core.messages import HumanMessage, SystemMessage

    system = SystemMessage(content="""You are a professional financial analyst assistant for a paper trading app.
You have access to price history, latest news and portfolio context tools.

ANALYSIS INSTRUCTIONS:
1. Always fetch price history first using get_price_history
2. Fetch recent news using get_ticker_news_tool and use it to inform sentiment signal
3. Fetch portfolio context using get_portfolio_context
4. After gathering all data, return ONLY a valid JSON object with NO additional text or markdown.

JSON RESPONSE FORMAT (must be valid JSON, no markdown, no extra text):
{
  "ticker": "string",
  "exchange": "string", 
  "latest_price": number,
  "trend_7d_pct": number,
  "trend_direction": "up" or "down",
  "sentiment_signal": "bullish" or "bearish" or "neutral" or "unavailable" (derived from recent news tone),
  "stance": "bull" or "bear" or "neutral",
  "summary": "string (3-4 sentences, plain English)",
  "confidence": "low" or "medium" or "high"
}

CRITICAL: After gathering all required data, output ONLY the JSON object. Do NOT make additional tool calls. Do NOT include any markdown formatting. Output valid JSON only.""")

    messages = [system] + state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    log.info(f"analyst node: {response}")
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
        "messages": [HumanMessage(content=f"Analyse {ticker} on {exchange} exchange for session {session_key}. After fetching all data, return ONLY valid JSON with no extra text.")],
        "ticker": ticker,
        "exchange": exchange,
        "session_key": session_key,
    })

    last_message = result["messages"][-1]
    
    if hasattr(last_message, "content") and last_message.content:
        content = last_message.content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {"raw": content, "error": "parse_failed"}
    
    return {"error": "no_content_from_agent", "raw": str(last_message)}