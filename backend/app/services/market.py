import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.models import StockPrice
from app.config import log

def filter_by_period(records: list, period: str) -> list:
    """Filter records to match the period. Period examples: '1mo', '3mo', '6mo', '1y'"""
    if not records:
        return records
    
    period_days = {
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
    }
    
    days = period_days.get(period, 90)  # Default to 3 months
    cutoff_date = datetime.now() - timedelta(days=days)
    
    return [r for r in records if r.date >= cutoff_date]


def format_ticker(ticker: str, exchange: str = "US") -> str:
    """
    US tickers stay as-is (AAPL, TSLA)
    Indian NSE: RELIANCE -> RELIANCE.NS
    Indian BSE: RELIANCE -> RELIANCE.BO
    Handles index aliases too.
    """
    ticker = ticker.upper().strip()

    # Global index aliases
    INDEX_MAP = {
        "NIFTY50": "^NSEI",
        "NIFTY": "^NSEI",
        "^NSEI": "^NSEI",

        "NASDAQ": "^IXIC",
        "NASDAQ100": "^NDX",
        "^IXIC": "^IXIC",

        "S&P500": "^GSPC",
        "SP500": "^GSPC",
        "^GSPC": "^GSPC",

        "DOW": "^DJI",
        "^DJI": "^DJI",
    }

    if ticker in INDEX_MAP:
        return INDEX_MAP[ticker]
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
    log.info(f"Downloading ticker={formatted}")

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

# replace get_live_quote entirely with:
def get_fast_quote(ticker: str, exchange: str) -> dict:
    """Uses fast_info — much lower latency than full info."""
    formatted = format_ticker(ticker, exchange)
    t = yf.Ticker(formatted)
    fi = t.fast_info

    return {
        "ticker": formatted,
        "price": fi.last_price,
        "prev_close": fi.previous_close,
        "open": fi.open,
        "day_high": fi.day_high,
        "day_low": fi.day_low,
        "volume": fi.last_volume,
        "market_cap": fi.market_cap,
        "currency": fi.currency,
        "exchange": fi.exchange,
    }


def get_ticker_news(ticker: str, exchange: str, count: int = 6) -> list[dict]:
    formatted = format_ticker(ticker, exchange)
    t = yf.Ticker(formatted)
    try:
        items = t.get_news(count=count)
        return [
            {
                "title": n.get("title"),
                "publisher": n.get("publisher"),
                "url": n.get("link"),
                "published_at": n.get("providerPublishTime"),
            }
            for n in items if n.get("title")
        ]
    except Exception:
        return []


def get_analyst_price_targets(ticker: str, exchange: str) -> dict:
    formatted = format_ticker(ticker, exchange)
    t = yf.Ticker(formatted)
    try:
        pt = t.get_analyst_price_targets()
        return {k: round(v, 2) for k, v in pt.items() if v is not None}
    except Exception:
        return {}


def get_upgrades_downgrades(ticker: str, exchange: str, limit: int = 8) -> list[dict]:
    formatted = format_ticker(ticker, exchange)
    t = yf.Ticker(formatted)
    try:
        df = t.get_upgrades_downgrades()
        if df is None or df.empty:
            return []
        df = df.head(limit).reset_index()
        return [
            {
                "date": str(row["GradeDate"])[:10],
                "firm": row["Firm"],
                "from_grade": row["FromGrade"],
                "to_grade": row["ToGrade"],
                "action": row["Action"],
            }
            for _, row in df.iterrows()
        ]
    except Exception:
        return []


def get_recommendations_summary(ticker: str, exchange: str) -> dict:
    formatted = format_ticker(ticker, exchange)
    t = yf.Ticker(formatted)
    try:
        df = t.get_recommendations_summary()
        if df is None or df.empty:
            return {}
        row = df.iloc[0]
        return {
            "strong_buy":  int(row.get("strongBuy", 0)),
            "buy":         int(row.get("buy", 0)),
            "hold":        int(row.get("hold", 0)),
            "sell":        int(row.get("sell", 0)),
            "strong_sell": int(row.get("strongSell", 0)),
        }
    except Exception:
        return {}