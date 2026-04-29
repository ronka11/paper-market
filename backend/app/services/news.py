import httpx
from app.config import settings

TAVILY_URL = "https://api.tavily.com/search"


async def search_news(
    query: str,
    max_results: int = 5,
    topic: str = "news",
    days: int = 3,
) -> list[dict]:

    payload = {
        "api_key": settings.TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "topic": topic,
        "days": days,
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
        "include_domains": [
            "reuters.com",
            "cnbc.com",
            "bloomberg.com",
            "finance.yahoo.com",
            "marketwatch.com",
            "wsj.com",
            "economictimes.indiatimes.com",
            "moneycontrol.com",
            "business-standard.com"
        ],
    }

    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(TAVILY_URL, json=payload)
        res.raise_for_status()
        data = res.json()

    cleaned = []

    for r in data.get("results", []):
        cleaned.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")[:300],
            "source": r.get("url", "").split("/")[2] if r.get("url") else ""
        })

    return cleaned


async def get_market_news(region: str = "GLOBAL") -> list[dict]:
    """
    region:
    GLOBAL / US / IN
    """
    if region.upper() == "US":
        query = ("US stock market today S&P 500 Nasdaq Dow Fed earnings inflation Reuters CNBC")

    elif region.upper() == "IN":
        query = ("India stock market today Nifty Sensex RBI FII DII earnings Moneycontrol Economic Times")

    else:
        query = ("global stock market today Fed ECB RBI inflation oil earnings Reuters Bloomberg")

    return await search_news(query, max_results=6)


async def get_ticker_news(ticker: str, exchange: str = "US") -> list[dict]:

    normalized = ticker.upper().strip()

    if exchange.upper() == "NSE" and not normalized.endswith(".NS"):
        normalized = f"{normalized}.NS"

    if exchange.upper() == "BSE" and not normalized.endswith(".BO"):
        normalized = f"{normalized}.BO"

    query = (
        f"{normalized} stock latest earnings analyst target news Reuters Yahoo Finance"
    )

    return await search_news(query, max_results=5)