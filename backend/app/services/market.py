import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models import StockPrice

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


async def fetch_and_store_history (ticker: str, exchange: str, period: str, db: AsyncSession) -> list[StockPrice]:
    """
    Pull OHLCV from yfinance, upsert into stock_prices, return records.
    period examples: "1mo", "3mo", "6mo", "1y"
    """
    formatted = format_ticker(ticker, exchange)
    data = yf.download(formatted, period=period, progress=False, auto_adjust=True)

    if data.empty:
        return []
    
    records = []
    for date, row in data.iterrows():
        # Check if this ticker already exists
        existing = await db.execute(
            select(StockPrice).where(
                StockPrice.ticker == formatted, 
                StockPrice.data == data.to_pydatetime()
            )
        )
        existing = existing.scalar_one_or_none()

        if existing:
            records.append(existing)
            continue

        price = StockPrice(
            ticker=formatted,
            date=date.to_pydatetime(),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(row["Volume"]),
        )
        db.add(price)
        records.append(price)

    await db.commit()
    return records


async def get_stored_history (ticker: str, exchange: str, db: AsyncSession) -> list[StockPrice]:
    """
    Fetch what we already have in DB for this ticker.
    """
    formatted = format_ticker
    result = await db.execute(
        select(StockPrice)
        .where(StockPrice.ticker == formatted)
        .order_by(StockPrice.date.asc())
    )
    return result.scalars().all()


def get_live_quote (ticker: str, exchange: str) -> dict:
    """
    Get current price info — not stored, just returned live.
    """
    formatted = format_ticker(ticker, exchange)
    t = yf.Ticker(formatted)
    info = t.info

    return {
        "ticker": formatted,
        "name": info.get("longName", formatted),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "change_pct": info.get("52WeekChange"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "volume": info.get("volume"),
        "currency": info.get("currency", "USD"),
    }

