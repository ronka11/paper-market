# Paper Simulator — Project Brief

## What it is
An AI-powered paper trading simulator. Feed it a stock/crypto ticker (Indian NSE/BSE or US), it pulls real market data + Reddit sentiment, runs algorithmic strategies, lets you simulate trades with virtual cash, and an LLM agent helps you reason about positions.

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend API | Python, FastAPI, uvicorn |
| Database | PostgreSQL + SQLAlchemy (async) + Alembic migrations |
| Market Data | yfinance — US tickers as-is, Indian as `RELIANCE.NS` / `TCS.BO` |
| Sentiment NLP | PRAW (Reddit scraper) + HuggingFace FinBERT |
| AI Agents | LangChain + LangGraph (multi-agent graph) + Groq or Gemini free tier |
| Task Queue | Celery + Redis (broker + result backend) |
| Frontend | React, raw CSS, Recharts for all charts |
| Session | No auth — browser `localStorage` UUID as session key |
| Hosting (later) | Raspberry Pi 4 4GB — Postgres + Redis + Celery workers via Docker Compose |

---

## System Architecture (3 layers)

**Layer 1 — React Frontend**
Five views: Portfolio Dashboard, Ticker View (charts + signals), AI Chat (agent interface), Sentiment Timeline, Backtest Results. Theme: e-ink aesthetic, monospace font, dark/light toggle. All state via localStorage.

**Layer 2 — FastAPI Backend**
- API Routers: `/market`, `/portfolio`, `/backtest`, `/sentiment`, `/agent`, `/news`
- Services: market (yfinance), portfolio (order execution, P&L), backtest (strategies), sentiment (PRAW + FinBERT), cache (Redis helpers)
- LangGraph Supervisor Agent routes queries to 4 specialist sub-agents: Market Agent, Sentiment Agent, Strategy Agent, Portfolio Agent. Each sub-agent has tools that call the FastAPI services directly.

**Layer 3 — Infrastructure**
- PostgreSQL (8 tables, Alembic managed)
- Redis (Celery broker on DB0, result backend on DB1, price cache)
- Celery Workers: pull market data hourly, scrape Reddit every 3h, run FinBERT scoring, handle async backtest jobs
- Celery Beat: cron-like scheduler for periodic tasks

---

## Database Schema (8 tables)

- `stock_prices` — OHLCV history, `Numeric(18,6)` for prices, composite unique on `(ticker, date)`, supports NSE/BSE/US
- `portfolios` — session_key (localStorage UUID), cash_balance, starting_cash, currency
- `positions` — one row per ticker per portfolio, quantity, avg_cost (weighted average), realised_pnl
- `orders` — immutable audit trail, side BUY/SELL, status PENDING/FILLED/CANCELLED/REJECTED, fill_price
- `reddit_posts` — raw scraped data, reddit_id unique, subreddit, posted_at
- `sentiment_scores` — FinBERT output (prob_positive, prob_negative, prob_neutral, compound score), linked 1:1 to reddit_posts
- `backtest_runs` — strategy config + aggregate metrics (Sharpe ratio, max drawdown, win rate, total return %)
- `backtest_trades` — per-trade equity curve data for charting, linked to backtest_runs

---

## Trading Strategies (3 to implement)
- Moving Average Crossover (short vs long window)
- RSI mean reversion
- Bollinger Band breakout

All three are backtestable against historical data with full P&L, Sharpe ratio, and max drawdown metrics.

---

## LangGraph Agent Design
Supervisor agent receives user query → routes to one or more specialist sub-agents → each sub-agent has LangChain tools that call internal FastAPI endpoints as tools. Pattern mirrors Agno's teams/experts model. LLM backend: Groq (fast free tier) or Gemini free tier.

Sub-agents and their tools:
- **Market Agent** — get_price, get_history, get_quote
- **Sentiment Agent** — get_sentiment_score, get_sentiment_trend
- **Strategy Agent** — run_signal, explain_strategy
- **Portfolio Agent** — get_positions, get_pnl, suggest_action

---

## Build Order (agreed sequence)
1. DB models + Postgres schema + Alembic setup ← done
2. Market service + market router (yfinance, NSE/BSE support, store OHLCV)
3. Portfolio service + portfolio router (order execution, P&L, Sharpe)
4. Celery + Redis setup (workers, beat scheduler, periodic tasks)
5. Sentiment pipeline (PRAW scraper + FinBERT scoring)
6. Backtest service (3 strategies, metrics calculation)
7. LangGraph agents (supervisor + 4 sub-agents, tool-calling)
8. React frontend (hooks first, then charts, then pages)
9. Deployement
10. NOT IN THIS PLAN: Deploy some stuff in RPI4

---

## Resume Bullet Points
- Built AI-powered paper trading platform with LangGraph multi-agent system integrating live market data, Reddit sentiment, and algorithmic signals
- Designed 3 backtestable trading strategies with P&L, Sharpe ratio, and max drawdown metrics
- Built NLP sentiment pipeline using FinBERT on Reddit financial communities, correlating social sentiment with price action
- Architected async FastAPI backend with PostgreSQL, Alembic migrations, and Redis-backed Celery task queue
- Built LangGraph supervisor agent with specialist sub-agents using tool-calling against live internal APIs