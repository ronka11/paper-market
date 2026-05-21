import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { useSession } from "../hooks/useSession"
import { fetchIndices, fetchPortfolio, fetchMarketNews } from "../api"
import { fetchScreener } from "../api"
import PriceChart from "../components/PriceChart"

export default function Dashboard() {
  const sessionKey = useSession()
  const [indices, setIndices]   = useState({ nifty50: [], nasdaq: [] })
  const [usPort, setUsPort]     = useState(null)
  const [inPort, setInPort]     = useState(null)
  const [news, setNews]         = useState([])
  const [currency, setCurrency] = useState("USD")
  const [loading, setLoading]   = useState(true)
  const [movers, setMovers] = useState([])

  const INR_RATE = 83.5  // fallback static rate, good enough for display

  useEffect(() => {
    if (!sessionKey) return
    async function load() {
      try {
        const [idx, us, ind, n] = await Promise.all([
          fetchIndices(sessionKey),
          fetchPortfolio(sessionKey, "US"),
          fetchPortfolio(sessionKey, "IN"),
          fetchMarketNews(sessionKey),
          fetchScreener("day_gainers").then(setMovers).catch(() => [])
        ])
        setIndices(idx)
        setUsPort(us)
        setInPort(ind)
        setNews(n.items || [])
      } catch (err) {
        console.error("dashboard load failed", err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [sessionKey])

  // Combined portfolio in chosen currency
  function combined() {
    if (!usPort || !inPort) return null
    const toUSD  = v => v
    const toINR  = v => v * INR_RATE
    const fromIN = v => currency === "USD" ? v / INR_RATE : v
    const fromUS = v => currency === "INR" ? toINR(v) : v

    const cash     = fromUS(usPort.cash_balance) + fromIN(inPort.cash_balance)
    const unreal   = fromUS(usPort.total_unrealised_pnl) + fromIN(inPort.total_unrealised_pnl)
    const real     = fromUS(usPort.total_realised_pnl)   + fromIN(inPort.total_realised_pnl)
    const sym      = currency === "USD" ? "$" : "₹"

    return { cash, unreal, real, sym }
  }

  if (loading) return <p className="muted" style={{ marginTop: "40px" }}>loading...</p>

  const combo = combined()

  return (
    <div>

      {/* ── Currency toggle ── */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
        {["USD", "INR"].map(c => (
          <button key={c} className={currency === c ? "btn" : "btn outline"}
            onClick={() => setCurrency(c)}
            style={{ padding: "4px 14px", fontSize: "12px" }}>
            {c}
          </button>
        ))}
        <span className="muted" style={{ fontSize: "11px", alignSelf: "center" }}>
          combined view · 1 USD = {INR_RATE} INR
        </span>
      </div>

      {/* ── Combined portfolio stats ── */}
      {combo && (
        <div className="card" style={{ marginBottom: "20px" }}>
          <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "14px" }}>
            COMBINED PORTFOLIO
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
            <Stat label="total cash"    value={`${combo.sym}${combo.cash.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
            <Stat label="unrealised"    value={`${combo.unreal >= 0 ? "+" : ""}${combo.sym}${combo.unreal.toFixed(2)}`} cls={combo.unreal >= 0 ? "up" : "down"} />
            <Stat label="realised"      value={`${combo.real >= 0 ? "+" : ""}${combo.sym}${combo.real.toFixed(2)}`}     cls={combo.real >= 0 ? "up" : "down"} />
            <Stat label="total p&l"     value={`${(combo.unreal + combo.real) >= 0 ? "+" : ""}${combo.sym}${(combo.unreal + combo.real).toFixed(2)}`} cls={(combo.unreal + combo.real) >= 0 ? "up" : "down"} />
          </div>
        </div>
      )}

      {/* ── Indices ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
        <IndexPanel title="NIFTY 50" data={indices.nifty50} />
        <IndexPanel title="NASDAQ"   data={indices.nasdaq}  />
      </div>

      {/* ── Individual portfolios ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
        <PortfolioPanel title="US PORTFOLIO" portfolio={usPort} currency="$" market="US" />
        <PortfolioPanel title="IN PORTFOLIO" portfolio={inPort} currency="₹" market="IN" />
      </div>
      

      {movers.length > 0 && (
        <div className="card" style={{ marginBottom: "20px" }}>
          <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "14px" }}>
            US DAY GAINERS
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "10px" }}>
            {movers.slice(0, 5).map(m => (
              <Link key={m.ticker} to={`/ticker/${m.ticker}`}
                style={{ textDecoration: "none", color: "var(--text-primary)" }}>
                <div style={{ borderBottom: "1px solid var(--border)", paddingBottom: "8px" }}>
                  <p style={{ fontSize: "12px", fontWeight: "bold" }}>{m.ticker}</p>
                  <p className="muted" style={{ fontSize: "11px", marginBottom: "4px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {m.name}
                  </p>
                  <p className="up" style={{ fontSize: "12px" }}>
                    +{m.change_pct?.toFixed(2)}%
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── News feed ── */}
      {news.length > 0 && (
        <div className="card">
          <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "14px" }}>
            MARKET NEWS · updated daily
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {news.map((item, i) => (
              <div key={i} style={{ borderBottom: "1px solid var(--border)", paddingBottom: "12px" }}>
                <a href={item.url} target="_blank" rel="noreferrer"
                  style={{ color: "var(--text-primary)", textDecoration: "none", fontSize: "13px", fontWeight: "bold" }}>
                  {item.title}
                </a>
                <p className="muted" style={{ fontSize: "12px", marginTop: "4px" }}>{item.snippet}</p>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}

function IndexPanel({ title, data }) {
  if (!data.length) return (
    <div className="card">
      <p style={{ fontWeight: "bold", fontSize: "13px", marginBottom: "12px" }}>{title}</p>
      <p className="muted" style={{ fontSize: "12px" }}>no data — run fetch_index_data task first</p>
    </div>
  )
  const latest = data[data.length - 1]
  const first  = data[0]
  const change = ((latest.close - first.close) / first.close) * 100

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
        <span style={{ fontWeight: "bold", fontSize: "13px" }}>{title}</span>
        <span className={change >= 0 ? "up" : "down"} style={{ fontSize: "13px" }}>
          {change >= 0 ? "+" : ""}{change.toFixed(2)}%
        </span>
      </div>
      <PriceChart data={data} height={150} mode="area" />
      <p className="muted" style={{ fontSize: "11px", marginTop: "6px", textAlign: "right" }}>
        last close {latest.close.toLocaleString()} · daily
      </p>
    </div>
  )
}

function PortfolioPanel({ title, portfolio, currency, market = "US" }) {
  if (!portfolio) return null
  const positions = portfolio.positions || []

  // Infer exchange from market: IN -> NSE, US -> US
  const defaultExchange = market === "IN" ? "NSE" : "US"

  return (
    <div className="card">
      <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "12px" }}>
        {title}
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
        <Stat label="cash"       value={`${currency}${portfolio.cash_balance.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
        <Stat label="unrealised" value={`${portfolio.total_unrealised_pnl >= 0 ? "+" : ""}${currency}${portfolio.total_unrealised_pnl.toFixed(2)}`}
          cls={portfolio.total_unrealised_pnl >= 0 ? "up" : "down"} />
      </div>
      {positions.length === 0
        ? <p className="muted" style={{ fontSize: "12px" }}>no positions</p>
        : positions.map(pos => (
          <div key={pos.ticker} style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
            <Link to={`/ticker/${pos.ticker}?exchange=${defaultExchange}`} style={{ color: "var(--text-primary)" }}>{pos.ticker}</Link>
            <span>{pos.quantity} shares</span>
            <span className={pos.unrealised_pnl >= 0 ? "up" : "down"}>
              {pos.unrealised_pnl >= 0 ? "+" : ""}{pos.unrealised_pnl.toFixed(2)}
            </span>
          </div>
        ))
      }
    </div>
  )
}

function Stat({ label, value, cls = "" }) {
  return (
    <div>
      <p className="muted" style={{ fontSize: "11px", marginBottom: "3px" }}>{label}</p>
      <p className={cls} style={{ fontSize: "15px" }}>{value}</p>
    </div>
  )
}