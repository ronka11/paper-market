import asyncio
import json
import yfinance as yf
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/prices")
async def live_prices(websocket: WebSocket):
    """
    Client sends: {"tickers": ["AAPL", "TSLA"]}
    Server streams: {"ticker": "AAPL", "price": 189.5, "change_pct": 1.2}
    every 3 seconds while connection is open.
    """
    await websocket.accept()

    tickers = []
    try:
        msg = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        data = json.loads(msg)
        tickers = data.get("tickers", [])
    except Exception:
        await websocket.close()
        return

    if not tickers:
        await websocket.close()
        return

    try:
        while True:
            for ticker in tickers:
                try:
                    t = yf.Ticker(ticker)
                    fi = t.fast_info
                    price = fi.last_price
                    prev  = fi.previous_close
                    change_pct = ((price - prev) / prev * 100) if prev else 0

                    await websocket.send_json({
                        "ticker":     ticker,
                        "price":      round(price, 4) if price else None,
                        "change_pct": round(change_pct, 3),
                    })
                except Exception:
                    # Ticker failed — send null so frontend knows
                    await websocket.send_json({"ticker": ticker, "price": None, "change_pct": None})

            await asyncio.sleep(3)

    except WebSocketDisconnect:
        pass