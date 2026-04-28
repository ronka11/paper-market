from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.market import get_stored_history, fetch_and_store_history
from app.services.news import get_ticker_news
from app.services.cache import get_cache, set_cache
from app.agents.analyst import llm

router = APIRouter()

SECTOR_SUGGESTIONS = {
    "tech":    [("AAPL", "MSFT"), ("GOOGL", "META"), ("NVDA", "AMD"), ("INFY.NS", "TCS.NS")],
    "banking": [("JPM", "BAC"), ("HDFCBANK.NS", "ICICIBANK.NS")],
    "energy":  [("XOM", "CVX"), ("RELIANCE.NS", "ONGC.NS")],
    "auto":    [("TSLA", "F"), ("MARUTI.NS", "TATAMOTORS.NS")],
    "defense": [("LMT", "RTX"), ("NOC", "GD")],
}


@router.get("/suggestions")
def get_suggestions():
    return SECTOR_SUGGESTIONS


@router.get("/")
async def compare(
    ticker_a: str,
    ticker_b: str,
    exchange_a: str = "US",
    exchange_b: str = "US",
    period: str = "3mo",
    x_session_key: str = Header(default="anonymous"),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"compare:{ticker_a}:{ticker_b}:{period}"
    cached = await get_cache(cache_key)
    if cached:
        return {**cached, "cached": True}

    # Fetch history for both
    hist_a = await get_stored_history(ticker_a, exchange_a, db)
    if not hist_a:
        hist_a = await fetch_and_store_history(ticker_a, exchange_a, period, db)

    hist_b = await get_stored_history(ticker_b, exchange_b, db)
    if not hist_b:
        hist_b = await fetch_and_store_history(ticker_b, exchange_b, period, db)

    if not hist_a or not hist_b:
        raise HTTPException(404, "Could not fetch history for one or both tickers")

    # Normalise to % change from first close
    def normalise(records):
        base = float(records[0].close)
        return [
            {"date": str(r.date.date()), "value": round(((float(r.close) - base) / base) * 100, 3)}
            for r in records
        ]

    # Fetch news for both (uses Tavily credits)
    news_a = await get_ticker_news(ticker_a)
    news_b = await get_ticker_news(ticker_b)

    # LLM comparison
    prompt = f"""Compare {ticker_a} and {ticker_b} as investments based on:
        Recent news for {ticker_a}: {news_a}
        Recent news for {ticker_b}: {news_b} and their fundamentals as a company and its history.
        Return JSON with keys: summary (3-4 sentences), winner (ticker string or "neutral"), reasoning (one sentence each for both tickers), 
            confidence (low/medium/high).
        If there are no clear winners mention that and its reasoning.
        Return ONLY JSON."""

    from langchain_core.messages import HumanMessage
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    import json
    try:
        analysis = json.loads(response.content)
    except Exception:
        analysis = {"raw": response.content}

    result = {
        "ticker_a": ticker_a,
        "ticker_b": ticker_b,
        "chart_a": normalise(hist_a),
        "chart_b": normalise(hist_b),
        "analysis": analysis,
    }

    await set_cache(cache_key, result, ttl_seconds=86400)
    return {**result, "cached": False}