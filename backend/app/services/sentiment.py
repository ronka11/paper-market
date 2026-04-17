# app/services/sentiment.py
import praw
import torch
import httpx
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.config import settings
from app.models import RedditPost, SentimentScore
from sqlalchemy.orm import selectinload

# ── Reddit client ─────────────────────────────────────────────────

def get_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
    )

# ── FinBERT (loaded once at module level, not per request) ────────

FINBERT_MODEL = "ProsusAI/finbert"
_tokenizer = None
_model = None

def get_finbert():
    global _tokenizer, _model
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL)
        _model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL)
        _model.eval()
    return _tokenizer, _model


def score_text(text: str) -> dict:
    """
    Run FinBERT on a piece of text.
    Returns probabilities for positive, negative, neutral.
    """
    tokenizer, model = get_finbert()

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1).squeeze().tolist()

    # FinBERT label order: positive, negative, neutral
    return {
        "prob_positive": probs[0],
        "prob_negative": probs[1],
        "prob_neutral":  probs[2],
        "compound":      probs[0] - probs[1],  # simple sentiment score
    }


# ── Scraper ───────────────────────────────────────────────────────

SUBREDDITS = ["stocks", "investing", "wallstreetbets", "IndiaInvestments", "IndianStreetBets"]
async def scrape_ticker(ticker: str, db: AsyncSession, limit: int = 10) -> list[RedditPost]:
    stored = []
    
    # 2026 Browser-emulation headers to bypass 403 blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.reddit.com/",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for subreddit_name in SUBREDDITS:
            url = f"https://www.reddit.com/r/{subreddit_name}/search.json"
            params = {
                "q": ticker,
                "sort": "new",
                "limit": limit,
                "restrict_sr": "on"
            }

            try:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    print(f"[sentiment] {subreddit_name} failed: {response.status_code}")
                    continue

                data = response.json()
                children = data.get("data", {}).get("children", [])

                for post_wrapper in children:
                    post = post_wrapper.get("data", {})
                    post_id = post.get("id")

                    # Deduplication check
                    existing = await db.execute(
                        select(RedditPost).where(RedditPost.reddit_id == post_id)
                    )
                    if existing.scalar_one_or_none():
                        continue

                    record = RedditPost(
                        reddit_id=post_id,
                        ticker=ticker.upper(),
                        subreddit=subreddit_name,
                        title=post.get("title"),
                        body=post.get("selftext", "")[:2000],
                        score=post.get("score", 0),
                        posted_at=datetime.utcfromtimestamp(post.get("created_utc")),
                    )
                    
                    db.add(record)
                    await db.flush() 
                    stored.append(record)

            except Exception as e:
                print(f"[sentiment] Error in r/{subreddit_name}: {e}")
                continue

    await db.commit()
    return stored


async def score_unscored_posts(db: AsyncSession) -> int:
    """
    Find all posts without a sentiment score, run FinBERT, store results.
    Returns count of posts scored.
    """
    result = await db.execute(
        select(RedditPost).where(~RedditPost.sentiment.has())
    )
    unscored = result.scalars().all()

    for post in unscored:
        text = f"{post.title}. {post.body or ''}"
        try:
            scores = score_text(text)
            sentiment = SentimentScore(post_id=post.id, **scores)
            db.add(sentiment)
        except Exception as e:
            print(f"[sentiment] scoring failed for post {post.id}: {e}")
            continue

    await db.commit()
    return len(unscored)


async def get_sentiment_summary(ticker: str, db: AsyncSession) -> dict:
    result = await db.execute(
        select(RedditPost)
        .options(selectinload(RedditPost.sentiment))  # 🔧 FIX
        .where(RedditPost.ticker == ticker.upper())
    )
    posts = result.scalars().all()

    if not posts:
        return {"ticker": ticker, "post_count": 0, "avg_compound": None}

    scored = [p for p in posts if p.sentiment]
    if not scored:
        return {"ticker": ticker, "post_count": len(posts), "avg_compound": None}

    avg_compound = sum(p.sentiment.compound for p in scored) / len(scored)
    avg_positive = sum(p.sentiment.prob_positive for p in scored) / len(scored)
    avg_negative = sum(p.sentiment.prob_negative for p in scored) / len(scored)

    return {
        "ticker": ticker.upper(),
        "post_count": len(posts),
        "scored_count": len(scored),
        "avg_compound": round(avg_compound, 4),
        "avg_positive": round(avg_positive, 4),
        "avg_negative": round(avg_negative, 4),
        "signal": "bullish" if avg_compound > 0.1 else "bearish" if avg_compound < -0.1 else "neutral",
    }