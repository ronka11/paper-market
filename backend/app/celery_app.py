from celery import Celery
from celery.schedules import crontab
from app.config import settings
# import app.tasks

celery = Celery(
    "paper_market",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery.autodiscover_tasks(["app"])

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    beat_schedule={
        # Pull prices for tracked tickers every 6 hours
        "fetch-prices-sixhourly": {
            "task": "app.tasks.fetch_prices_for_all_tickers",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        # Scrape Reddit every 24 hours
        "scrape-reddit-24h": {
            "task": "app.tasks.scrape_reddit_for_all_tickers",
            "schedule": crontab(minute=0, hour="*/24"),
        },
        # add to beat_schedule
        "fetch-indices-daily": {
            "task": "app.tasks.fetch_index_data",
            "schedule": crontab(hour=1, minute=0),  # 1am UTC daily
        },
    },
)