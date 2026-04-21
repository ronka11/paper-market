from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.cache import get_cache, set_cache
from app.agents.analyst import run_analysis

router = APIRouter()

CACHE_TTL = 86400  # 24 hours


@router.get("/analyse/{ticker}")
async def analyse_ticker(
    ticker: str,
    exchange: str = "US",
    force_refresh: bool = False,
    x_session_key: str = Header(default="anonymous"),
):
    cache_key = f"analysis:{ticker}:{exchange}"

    if not force_refresh:
        cached = await get_cache(cache_key)
        if cached:
            return {**cached, "cached": True}

    try:
        analysis = await run_analysis(ticker, exchange, x_session_key)
    except Exception as e:
        raise HTTPException(500, f"Agent failed: {str(e)}")

    if "error" not in analysis:
        await set_cache(cache_key, analysis, ttl_seconds=CACHE_TTL)

    return {**analysis, "cached": False}


@router.get("/indices")
async def get_indices(db: AsyncSession = Depends(get_db)):
    """
    Return stored history for Nifty50 and Nasdaq.
    Refreshed daily by Celery — no live calls here.
    """
    from app.services.market import get_stored_history

    nifty = await get_stored_history("^NSEI", "US", db)
    nasdaq = await get_stored_history("^IXIC", "US", db)

    def serialize(records):
        return [
            {"date": str(r.date.date()), "close": float(r.close)}
            for r in records[-90:]  # last 90 days for the chart
        ]

    return {
        "nifty50": serialize(nifty),
        "nasdaq": serialize(nasdaq),
    }