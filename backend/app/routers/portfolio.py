from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import portfolio as portfolio_service
from app.services import market as market_service

router = APIRouter()


def get_session_key(x_session_key: str = Header(...)) -> str:
    """Browser sends its localStorage UUID as X-Session-Key header."""
    return x_session_key


class OrderRequest(BaseModel):
    ticker: str
    exchange: str = "US"
    side: str     # BUY or SELL
    quantity: int
    use_live_price: bool = True
    limit_price: float | None = None


@router.get("/")
async def get_portfolio(
    session_key: str = Depends(get_session_key),
    db: AsyncSession = Depends(get_db)):

    portfolio = await portfolio_service.get_or_create_portfolio(session_key, db)
    positions = await portfolio_service.get_positions(portfolio.id, db)

    # Fetch live prices for all held tickers
    current_prices = {}
    for pos in positions:
        try:
            quote = market_service.get_live_quote(pos.ticker, "US")
            current_prices[pos.ticker] = quote["price"] or 0
        except Exception:
            current_prices[pos.ticker] = 0

    pnl = portfolio_service.calculate_pnl(positions, current_prices)

    return {
        "portfolio_id": portfolio.id,
        "cash_balance": float(portfolio.cash_balance),
        "starting_cash": float(portfolio.starting_cash),
        "currency": portfolio.currency,
        **pnl
    }


@router.post("/order")
async def place_order(
    body: OrderRequest,
    session_key: str = Depends(get_session_key),
    db: AsyncSession = Depends(get_db)
):
    if body.side not in ("BUY", "SELL"):
        raise HTTPException(400, "side must be BUY or SELL")
    if body.quantity <= 0:
        raise HTTPException(400, "quantity must be positive")

    portfolio = await portfolio_service.get_or_create_portfolio(session_key, db)

    # Determine fill price
    if body.use_live_price:
        try:
            quote = market_service.get_live_quote(body.ticker, body.exchange)
            fill_price = quote["price"]
        except Exception:
            raise HTTPException(500, "Could not fetch live price")
    else:
        if not body.limit_price:
            raise HTTPException(400, "limit_price required when use_live_price is false")
        fill_price = body.limit_price

    order = await portfolio_service.place_order(
        portfolio, body.ticker, body.side, body.quantity, fill_price, db
    )

    return {
        "order_id": order.id,
        "status": order.status,
        "fill_price": float(order.fill_price),
        "ticker": order.ticker,
        "side": order.side,
        "quantity": order.quantity,
    }


@router.get("/orders")
async def get_orders(
    session_key: str = Depends(get_session_key),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await portfolio_service.get_or_create_portfolio(session_key, db)
    orders = await portfolio_service.get_orders(portfolio.id, db)
    return [
        {
            "id": o.id,
            "ticker": o.ticker,
            "side": o.side,
            "quantity": o.quantity,
            "fill_price": float(o.fill_price) if o.fill_price else None,
            "status": o.status,
            "created_at": o.created_at,
        }
        for o in orders
    ]