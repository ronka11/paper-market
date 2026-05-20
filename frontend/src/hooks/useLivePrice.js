import { useState, useEffect, useRef } from "react"

const WS_URL = "ws://localhost:8000/ws/prices"

export function useLivePrice(tickers = []) {
  const [prices, setPrices] = useState({})
  const wsRef = useRef(null)

  useEffect(() => {
    if (!tickers.length) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({ tickers }))
    }

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.ticker && data.price !== null) {
        setPrices(prev => ({ ...prev, [data.ticker]: data }))
      }
    }

    ws.onerror = () => ws.close()

    return () => ws.close()
  }, [tickers.join(",")])

  return prices
}