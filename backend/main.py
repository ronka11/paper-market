# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import market

app = FastAPI(title="Paper Market API", debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers mounted here as we build them
# from app.routers import market, portfolio
# app.include_router(market.router, prefix="/market")

@app.get("/health") 
async def health():
    return {"status": "ok"}

# MARKET
app.include_router(market.router, prefix="/market", tags=["market"])


# PORTFOLIO
from app.routers import market, portfolio

app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])


# SENTIMENT
from app.routers import market, portfolio, sentiment

app.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])


# AGENTS
from app.routers import market, portfolio, sentiment, agent

app.include_router(agent.router, prefix="/agent", tags=["agent"])