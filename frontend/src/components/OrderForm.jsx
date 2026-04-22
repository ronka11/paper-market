// src/components/OrderForm.jsx
import { useState } from "react"
import { placeOrder } from "../api"

export default function OrderForm({ ticker, exchange, sessionKey, onOrderPlaced }) {
  const [side, setSide] = useState("BUY")
  const [quantity, setQuantity] = useState(1)
  const [useLive, setUseLive] = useState(true)
  const [limitPrice, setLimitPrice] = useState("")
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setStatus(null)

    try {
      const order = {
        ticker,
        exchange,
        side,
        quantity: parseInt(quantity),
        use_live_price: useLive,
        limit_price: useLive ? null : parseFloat(limitPrice),
      }
      const result = await placeOrder(order, sessionKey)
      setStatus({ ok: result.status === "FILLED", message: `${result.status} @ ${result.fill_price}` })
      if (result.status === "FILLED" && onOrderPlaced) onOrderPlaced()
    } catch (err) {
      setStatus({ ok: false, message: err.response?.data?.detail || "order failed" })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <p style={{ fontWeight: "bold", fontSize: "13px", marginBottom: "14px" }}>PLACE ORDER</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ display: "flex", gap: "8px" }}>
          {["BUY", "SELL"].map(s => (
            <button
              key={s} type="button"
              className={side === s ? "btn" : "btn outline"}
              onClick={() => setSide(s)}
              style={{ flex: 1, background: side === s ? (s === "BUY" ? "var(--green)" : "var(--red)") : "transparent" }}
            >
              {s}
            </button>
          ))}
        </div>

        <div>
          <label className="muted" style={{ fontSize: "12px" }}>quantity</label>
          <input
            type="number" min="1" value={quantity}
            onChange={e => setQuantity(e.target.value)}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            type="checkbox" id="live-price" checked={useLive}
            onChange={e => setUseLive(e.target.checked)}
            style={{ width: "auto" }}
          />
          <label htmlFor="live-price" className="muted" style={{ fontSize: "12px" }}>use live price</label>
        </div>

        {!useLive && (
          <div>
            <label className="muted" style={{ fontSize: "12px" }}>limit price</label>
            <input
              type="number" step="0.01" value={limitPrice}
              onChange={e => setLimitPrice(e.target.value)}
              placeholder="0.00"
            />
          </div>
        )}

        <button type="submit" className="btn" disabled={loading}>
          {loading ? "placing..." : `${side} ${quantity} × ${ticker}`}
        </button>

        {status && (
          <p style={{ fontSize: "12px", color: status.ok ? "var(--green)" : "var(--red)" }}>
            {status.message}
          </p>
        )}
      </form>
    </div>
  )
}