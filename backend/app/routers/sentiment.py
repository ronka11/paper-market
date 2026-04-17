from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import sentiment as sentiment_service
from app.tasks import scrape_reddit_for_ticker

router = APIRouter()


@router.post("/scrape/{ticker}")
async def trigger_scrape(ticker: str):
    """Kick off a background scrape for a ticker via Celery."""
    task = scrape_reddit_for_ticker.delay(ticker)
    return {"task_id": task.id, "ticker": ticker, "status": "queued"}


@router.post("/score")
async def trigger_scoring(db: AsyncSession = Depends(get_db)):
    """Score all unscored posts in DB."""
    count = await sentiment_service.score_unscored_posts(db)
    return {"scored": count}


@router.get("/summary/{ticker}")
async def get_summary(ticker: str, db: AsyncSession = Depends(get_db)):
    summary = await sentiment_service.get_sentiment_summary(ticker, db)
    if summary["post_count"] == 0:
        raise HTTPException(404, f"No posts found for {ticker}. Try scraping first.")
    return summary