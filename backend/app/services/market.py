import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models import StockPrice
from app.config import log

def format_ticker(ticker: str, exchange: str = "US") -> str:
    """
    US tickers stay as-is (AAPL, TSLA)
    Indian NSE: RELIANCE -> RELIANCE.NS
    Indian BSE: RELIANCE -> RELIANCE.BO
    """
    ticker = ticker.upper().strip()
    if exchange == "NSE":
        return f"{ticker}.NS"
    elif exchange == "BSE":
        return f"{ticker}.BO"
    return ticker


async def fetch_and_store_history (
        ticker: str, 
        exchange: str, 
        period: str, 
        db: AsyncSession) -> list[StockPrice]:
    """
    Pull OHLCV from yfinance, upsert into stock_prices, return records.
    period examples: "1mo", "3mo", "6mo", "1y"
    """
    formatted = format_ticker(ticker, exchange)

    data = yf.download(formatted, period=period, progress=False, auto_adjust=True)

    if data.empty:
        return []

    if hasattr(data.columns, "levels"):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()


    # 1 query → get all existing dates
    # Loop → in-memory checks (set)
    # 1 batch insert
    # 1 query → fetch results
    result = await db.execute(
        select(StockPrice.date).where(StockPrice.ticker == formatted)
    )
    existing_dates = set(result.scalars().all())

    new_records = []
    all_records = []

    for row in data.itertuples():
        dt = row.Date.to_pydatetime()

        if dt in existing_dates:
            continue

        price = StockPrice(
            ticker=formatted,
            date=dt,
            open=float(row.Open),
            high=float(row.High),
            low=float(row.Low),
            close=float(row.Close),
            volume=int(row.Volume),
        )

        new_records.append(price)
        all_records.append(price)

    if new_records:
        db.add_all(new_records)
        await db.commit()

    result = await db.execute(
        select(StockPrice)
        .where(StockPrice.ticker == formatted)
        .order_by(StockPrice.date.asc())
    )

    log.info(f"fetch_and_store_history: {result}")
    return result.scalars().all()


async def get_stored_history (ticker: str, exchange: str, db: AsyncSession) -> list[StockPrice]:
    """
    Fetch what we already have in DB for this ticker.
    """
    formatted = format_ticker(ticker, exchange)
    result = await db.execute(
        select(StockPrice)
        .where(StockPrice.ticker == formatted)
        .order_by(StockPrice.date.asc())
    )
    log.info(f"get_stored_history: {result}")
    return result.scalars().all()


def get_live_quote (ticker: str, exchange: str) -> dict:
    """
    Get current price info — not stored, just returned live.
    """
    formatted = format_ticker(ticker, exchange)
    t = yf.Ticker(formatted)
    info = t.info

    live_quote_res = {
        "ticker": formatted,
        "name": info.get("longName", formatted),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "change_pct": info.get("52WeekChange"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "volume": info.get("volume"),
        "currency": info.get("currency", "USD"),
    }
    return live_quote_res