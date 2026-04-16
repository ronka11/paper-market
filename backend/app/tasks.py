import asyncio
from sqlalchemy import select
from app.celery_app import celery
from app.database import AsyncSessionLocal
from app.models import Portfolio, Position


def run_async(coro):
    """Helper — Celery workers are sync, so we run async code with this."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _get_all_tracked_tickers() -> list[str]:
    """
    Find every ticker currently held across all portfolios.
    These are the ones worth keeping fresh.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Position.ticker).distinct())
        return result.scalars().all()


# Price fetching 

@celery.task(name="app.tasks.fetch_prices_for_all_tickers")
def fetch_prices_for_all_tickers():
    async def _run():
        from app.services.market import fetch_and_store_history
        tickers = await _get_all_tracked_tickers()

        if not tickers:
            return {"fetched": 0}

        async with AsyncSessionLocal() as db:
            for ticker in tickers:
                # Ticker already has exchange suffix (.NS / .BO / plain)
                exchange = "NSE" if ticker.endswith(".NS") else \
                           "BSE" if ticker.endswith(".BO") else "US"
                base = ticker.replace(".NS", "").replace(".BO", "")
                await fetch_and_store_history(base, exchange, "1mo", db)

        return {"fetched": len(tickers)}

    return run_async(_run())


@celery.task(name="app.tasks.fetch_prices_for_ticker")
def fetch_prices_for_ticker(ticker: str, exchange: str = "US"):
    """Manually trigger a price refresh for one ticker."""
    async def _run():
        from app.services.market import fetch_and_store_history
        async with AsyncSessionLocal() as db:
            records = await fetch_and_store_history(ticker, exchange, "3mo", db)
        return {"ticker": ticker, "records_stored": len(records)}

    return run_async(_run())


# Reddit scraping : under development

@celery.task(name="app.tasks.scrape_reddit_for_all_tickers")
def scrape_reddit_for_all_tickers():
    async def _run():
        from app.services.sentiment import scrape_ticker
        tickers = await _get_all_tracked_tickers()

        if not tickers:
            return {"scraped": 0}

        # Strip exchange suffix for Reddit search — search "RELIANCE" not "RELIANCE.NS"
        base_tickers = [t.replace(".NS", "").replace(".BO", "") for t in tickers]

        async with AsyncSessionLocal() as db:
            for ticker in base_tickers:
                await scrape_ticker(ticker, db)

        return {"scraped": len(base_tickers)}

    return run_async(_run())


@celery.task(name="app.tasks.scrape_reddit_for_ticker")
def scrape_reddit_for_ticker(ticker: str):
    """Manually trigger Reddit scrape for one ticker."""
    async def _run():
        from app.services.sentiment import scrape_ticker
        async with AsyncSessionLocal() as db:
            posts = await scrape_ticker(ticker, db)
        return {"ticker": ticker, "posts_stored": len(posts)}

    return run_async(_run())