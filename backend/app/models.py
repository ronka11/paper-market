# backend/app/models.py
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String, Numeric, Integer, DateTime, ForeignKey,
    UniqueConstraint, Enum, Text, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def now(): return datetime.utcnow()
def new_uuid(): return str(uuid.uuid4())


class StockPrice(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (UniqueConstraint("ticker", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    volume: Mapped[int] = mapped_column(Integer)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_key: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("100000"))
    starting_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("100000"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    positions: Mapped[list["Position"]] = relationship(back_populates="portfolio")
    orders: Mapped[list["Order"]] = relationship(back_populates="portfolio")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("portfolio_id", "ticker"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    ticker: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal("0"))
    realised_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"))
    ticker: Mapped[str] = mapped_column(String(20))
    side: Mapped[str] = mapped_column(Enum("BUY", "SELL", name="order_side"))
    quantity: Mapped[int] = mapped_column(Integer)
    fill_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "FILLED", "CANCELLED", "REJECTED", name="order_status"),
        default="PENDING"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="orders")


class RedditPost(Base):
    __tablename__ = "reddit_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reddit_id: Mapped[str] = mapped_column(String(20), unique=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    subreddit: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    posted_at: Mapped[datetime] = mapped_column(DateTime)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    sentiment: Mapped["SentimentScore"] = relationship(back_populates="post", uselist=False)


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("reddit_posts.id"), unique=True)
    prob_positive: Mapped[float] = mapped_column(Float)
    prob_negative: Mapped[float] = mapped_column(Float)
    prob_neutral: Mapped[float] = mapped_column(Float)
    compound: Mapped[float] = mapped_column(Float)   # positive - negative
    scored_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    post: Mapped["RedditPost"] = relationship(back_populates="sentiment")


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20))
    strategy: Mapped[str] = mapped_column(String(50))   # ma_crossover | rsi | bollinger
    params: Mapped[str] = mapped_column(Text)            # JSON string of strategy params
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=True)
    win_rate: Mapped[float] = mapped_column(Float, nullable=True)
    total_return_pct: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    trades: Mapped[list["BacktestTrade"]] = relationship(back_populates="run")


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"))
    date: Mapped[datetime] = mapped_column(DateTime)
    side: Mapped[str] = mapped_column(String(4))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    quantity: Mapped[int] = mapped_column(Integer)
    equity: Mapped[Decimal] = mapped_column(Numeric(18, 2))  # portfolio value at this point

    run: Mapped["BacktestRun"] = relationship(back_populates="trades")