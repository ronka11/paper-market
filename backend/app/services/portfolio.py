from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Portfolio, Position, Order
from app.config import log

async def get_or_create_portfolio(
        session_key: str,
        db: AsyncSession) -> Portfolio:
    '''
    Creates/fetches portfolio
    '''
    result = await db.execute(
        select(Portfolio).
        where(Portfolio.session_key == session_key)
    )
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        portfolio = Portfolio(session_key=session_key)
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)

    log.info("portfolio created/fetched")
    return portfolio


async def get_positions(
        portfolio_id: str,
        db: AsyncSession) -> list[Position]:
    result = await db.execute(
        select(Position).
        where(Position.portfolio_id == portfolio_id)
    )
    log.info("get_positions called")
    return result.scalars().all()


async def get_orders(
        portfolio_id: str, 
        db: AsyncSession) -> list[Order]:
    result = await db.execute(
        select(Order).where(Order.portfolio_id == portfolio_id)
        .order_by(Order.created_at.desc())
    )
    log.info("get_orders called")
    return result.scalars().all()


async def place_order(
        portfolio: Portfolio,
        ticker: str, 
        side: str,
        quantity: int,
        fill_price: float,
        db: AsyncSession) -> Order:
    fill_price = Decimal(str(fill_price))
    total_cost = fill_price * quantity

    # create the order record first
    order = Order(
        portfolio_id=portfolio.id,
        ticker=ticker,
        side=side,
        quantity=quantity,
        fill_price=fill_price,
        status="PENDING"
    )
    db.add(order)

    if side == "BUY":
        if portfolio.cash_balance < total_cost:
            order.status = "REJECTED"
            await db.commit()
            log.info("order REJECTED - portfolio.cash_balance < total_cost")
            return order
        
        portfolio.cash_balance -= total_cost
        await _upsert_position_buy(portfolio.id, ticker, quantity, fill_price, db)

    elif side == "SELL":
        position = await _get_position(portfolio.id, ticker, db)

        if not position or position.quantity < quantity:
            order.status = "REJECTED"
            await db.commit()
            log.info("order REJECTED - position.quantity < quantity")
            return order
        
        portfolio.cash_balance += total_cost
        await _upsert_position_sell(position, quantity, fill_price, db)

    order.status = "FILLED"
    await db.commit()
    await db.refresh(order)
    log.info("order FILLED")
    return order


async def _get_position(
        portfolio_id: str, 
        ticker: str,
        db: AsyncSession):
    result = await db.execute(
        select(Position).
        where(
            Position.portfolio_id == portfolio_id,
            Position.ticker == ticker
        )
    )
    return result.scalar_one_or_none()


async def _upsert_position_buy(
        portfolio_id: str, 
        ticker: str, 
        quantity: int,
        fill_price: Decimal,
        db: AsyncSession):
    position = await _get_position(portfolio_id, ticker, db)

    if position:
        # weighted average cost
        total_qty = position.quantity + quantity
        position.avg_cost = (
            (position.avg_cost * position.quantity) + (fill_price * quantity)
        ) / total_qty
    else:
        position = Position(
            portfolio_id=portfolio_id,
            ticker=ticker,
            quantity=quantity,
            avg_cost=fill_price
        )
        db.add(position)


async def _upsert_position_sell(
        portfolio_id: str,
        position: Position, 
        # ticker: str, 
        quantity: int,
        fill_price: Decimal,
        db: AsyncSession):
    realised = (fill_price - position.avg_cost) * quantity
    position.realised_pnl += realised
    position.quantity -= quantity

    # clean up zero positions
    if position.quantity == 0:
        await db.delete(position)


def calculate_pnl(
        position: list[Position],
        current_prices: dict[str, float]) -> dict:
    """
    current_prices: { "AAPL": 189.5, "RELIANCE.NS": 2840.0 }
    Returns unrealised P&L per position and total portfolio stats.
    """
    breakdown = []
    total_unrealised = Decimal("0")
    total_realised = Decimal("0")

    for pos in position:
        current = Decimal(str(current_prices.get(pos.ticker, 0)))
        unrealised = (current - pos.avg_cost) * pos.quantity
        total_unrealised += unrealised
        total_realised += pos.realised_pnl

        breakdown.append({
            "ticker": pos.ticker,
            "quantity": pos.quantity,
            "avg_cost": float(pos.avg_cost),
            "current_price": float(current),
            "unrealised_pnl": float(unrealised),
            "realised_pnl": float(pos.realised_pnl),
        })

    pnl_res = {
        "positions": breakdown,
        "total_unrealised_pnl": float(total_unrealised),
        "total_realised_pnl": float(total_realised),
    }
    log.info(f"calculate_pnl: {pnl_res}")
    return pnl_res