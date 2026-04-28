import httpx
from app.config import settings

TAVILY_URL = "https://api.tavily.com/search"

async def search_news(query: str, max_results: int = 5) -> list[dict]:
    async with httpx.AsyncClient() as client:
        res = await client.post(TAVILY_URL, json={
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
        })
        data = res.json()
    return [
        {"title": r["title"], "url": r["url"], "snippet": r.get("content", "")[:200]}
        for r in data.get("results", [])
    ]


async def get_market_news() -> list[dict]:
    """Daily market news — called by Celery, cached in Redis."""
    return await search_news("stock market financial news today", max_results=6)


async def get_ticker_news(ticker: str) -> list[dict]:
    """Per-ticker news — called during AI analysis only."""
    return await search_news(f"{ticker} stock news", max_results=3)