from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import market as market_service
from app.config import log

router = APIRouter()

VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y"}
VALID_EXCHANGES = {"US", "NSE", "BSE"}


# replace /quote endpoint:
@router.get("/quote")
async def get_quote(ticker: str, exchange: str = Query(default="US")):
    if exchange not in VALID_EXCHANGES:
        raise HTTPException(400, f"exchange must be one of {VALID_EXCHANGES}")
    try:
        return market_service.get_fast_quote(ticker, exchange)
    except Exception as e:
        raise HTTPException(500, str(e))


# add these new endpoints at the bottom:
@router.get("/news")
async def get_ticker_news(
    ticker: str,
    exchange: str = Query(default="US"),
):
    return market_service.get_ticker_news(ticker, exchange)


@router.get("/price-targets")
async def get_price_targets(
    ticker: str,
    exchange: str = Query(default="US"),
):
    return market_service.get_analyst_price_targets(ticker, exchange)


@router.get("/upgrades-downgrades")
async def get_upgrades_downgrades(
    ticker: str,
    exchange: str = Query(default="US"),
):
    return market_service.get_upgrades_downgrades(ticker, exchange)


@router.get("/recommendations")
async def get_recommendations(
    ticker: str,
    exchange: str = Query(default="US"),
):
    return market_service.get_recommendations_summary(ticker, exchange)
    

@router.get("/history")
async def get_history(
    ticker: str,
    exchange: str = Query(default="US"),
    period: str = Query(default="3mo"),
    refresh: bool = Query(default=False),
    db: AsyncSession = Depends(get_db)
):
    if exchange not in VALID_EXCHANGES:
        raise HTTPException(400, f"exchange must be one of {VALID_EXCHANGES}")
    if period not in VALID_PERIODS:
        raise HTTPException(400, f"period must be one of {VALID_PERIODS}")
    
    if refresh:
        records = await market_service.fetch_and_store_history(ticker, exchange, period, db)
    else:
        records = await market_service.get_stored_history(ticker, exchange, db)
        if not records:
            records = await market_service.fetch_and_store_history(ticker, exchange, period, db)
    
    # Filter records by the requested period
    records = market_service.filter_by_period(records, period)

    return [
        {
            "date": r.date,
            "open": float(r.open),
            "high": float(r.high),
            "low": float(r.low),
            "close": float(r.close),
            "volume": r.volume,
        }
        for r in records
    ]