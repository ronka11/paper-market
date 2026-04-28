// src/pages/Compare.jsx
import { useState, useEffect } from "react"
import { useSession } from "../hooks/useSession"
import { fetchComparisons, fetchCompare } from "../api"
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts"

export default function Compare() {
  const sessionKey = useSession()
  const [suggestions, setSuggestions] = useState({})
  const [tickerA, setTickerA]         = useState("")
  const [tickerB, setTickerB]         = useState("")
  const [exchangeA, setExchangeA]     = useState("US")
  const [exchangeB, setExchangeB]     = useState("US")
  const [result, setResult]           = useState(null)
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState(null)

  useEffect(() => {
    if (!sessionKey) return
    fetchComparisons(sessionKey).then(setSuggestions).catch(console.error)
  }, [sessionKey])

  function applySuggestion(a, b) {
    const exchA = a.endsWith(".NS") || a.endsWith(".BO") ? (a.endsWith(".NS") ? "NSE" : "BSE") : "US"
    const exchB = b.endsWith(".NS") || b.endsWith(".BO") ? (b.endsWith(".NS") ? "NSE" : "BSE") : "US"
    setTickerA(a.replace(".NS","").replace(".BO",""))
    setTickerB(b.replace(".NS","").replace(".BO",""))
    setExchangeA(exchA)
    setExchangeB(exchB)
  }

  async function handleCompare(e) {
    e.preventDefault()
    if (!tickerA || !tickerB) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await fetchCompare(tickerA, exchangeA, tickerB, exchangeB, "3mo", sessionKey)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || "comparison failed")
    } finally {
      setLoading(false)
    }
  }

  // Merge two series by date for Recharts
  function mergeCharts(a, b, labelA, labelB) {
    const map = {}
    a.forEach(d => { map[d.date] = { date: d.date, [labelA]: d.value } })
    b.forEach(d => { map[d.date] = { ...map[d.date], date: d.date, [labelB]: d.value } })
    return Object.values(map).sort((x, y) => x.date.localeCompare(y.date))
  }

  return (
    <div>
      <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "20px" }}>
        COMPARE STOCKS
      </p>

      {/* ── Suggestions ── */}
      <div className="card" style={{ marginBottom: "20px" }}>
        <p className="muted" style={{ fontSize: "12px", marginBottom: "12px" }}>suggested pairs by sector</p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
          {Object.entries(suggestions).map(([sector, pairs]) =>
            pairs.map(([a, b], i) => (
              <button key={`${sector}-${i}`} className="btn outline"
                onClick={() => applySuggestion(a, b)}
                style={{ fontSize: "11px", padding: "4px 10px" }}>
                {a.replace(".NS","").replace(".BO","")} vs {b.replace(".NS","").replace(".BO","")}
                <span className="muted" style={{ marginLeft: "6px" }}>{sector}</span>
              </button>
            ))
          )}
        </div>
      </div>

      {/* ── Input form ── */}
      <div className="card" style={{ marginBottom: "20px" }}>
        <form onSubmit={handleCompare} style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr auto", gap: "10px", alignItems: "end" }}>
          <div>
            <label className="muted" style={{ fontSize: "11px" }}>ticker A</label>
            <input value={tickerA} onChange={e => setTickerA(e.target.value.toUpperCase())} placeholder="AAPL" />
          </div>
          <select value={exchangeA} onChange={e => setExchangeA(e.target.value)} style={{ width: "80px" }}>
            <option value="US">US</option>
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
          </select>
          <div>
            <label className="muted" style={{ fontSize: "11px" }}>ticker B</label>
            <input value={tickerB} onChange={e => setTickerB(e.target.value.toUpperCase())} placeholder="MSFT" />
          </div>
          <select value={exchangeB} onChange={e => setExchangeB(e.target.value)} style={{ width: "80px" }}>
            <option value="US">US</option>
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
          </select>
          <button type="submit" className="btn" disabled={loading}
            style={{ gridColumn: "span 4" }}>
            {loading ? "comparing..." : `compare ${tickerA || "A"} vs ${tickerB || "B"}`}
          </button>
        </form>
        {error && <p style={{ color: "var(--red)", fontSize: "12px", marginTop: "10px" }}>{error}</p>}
      </div>

      {/* ── Result ── */}
      {result && (
        <>
          {/* Normalised chart */}
          <div className="card" style={{ marginBottom: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
              <span style={{ fontSize: "13px", fontWeight: "bold" }}>
                {result.ticker_a} vs {result.ticker_b} · % change
              </span>
              {result.cached && <span className="tag neutral">cached</span>}
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={mergeCharts(result.chart_a, result.chart_b, result.ticker_a, result.ticker_b)}
                margin={{ top: 4, right: 4, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "var(--text-secondary)", fontFamily: "var(--font)" }}
                  tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 11, fill: "var(--text-secondary)", fontFamily: "var(--font)" }}
                  tickLine={false} axisLine={false}
                  tickFormatter={v => `${v > 0 ? "+" : ""}${v.toFixed(1)}%`} />
                <Tooltip
                  contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", fontFamily: "var(--font)", fontSize: "12px" }}
                  formatter={(v, name) => [`${v > 0 ? "+" : ""}${v.toFixed(2)}%`, name]}
                />
                <Legend wrapperStyle={{ fontSize: "12px", fontFamily: "var(--font)" }} />
                <Line type="monotone" dataKey={result.ticker_a} stroke="#4caf50" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey={result.ticker_b} stroke="#e57373" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* AI analysis */}
          {result.analysis && (
            <div className="card">
              {result.analysis.raw ? (
                <p className="muted" style={{ fontSize: "12px" }}>analysis parse error (raw response)</p>
              ) : (
                <>
                  <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "14px" }}>
                    <span style={{ fontSize: "13px", fontWeight: "bold" }}>AI COMPARISON</span>
                    {result.analysis.winner && result.analysis.winner !== "neutral" && (
                      <span className="tag bull">{result.analysis.winner} leads</span>
                    )}
                    {result.analysis.confidence && (
                      <span className="tag neutral">confidence: {result.analysis.confidence}</span>
                    )}
                  </div>
                  <p style={{ fontSize: "13px", lineHeight: "1.8", marginBottom: "14px" }}>
                    {result.analysis.summary}
                  </p>
                  {result.analysis.reasoning && (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                      {Object.entries(result.analysis.reasoning).map(([ticker, text]) => (
                        <div key={ticker} style={{ borderLeft: "2px solid var(--border)", paddingLeft: "10px" }}>
                          <p style={{ fontSize: "11px", letterSpacing: "0.06em", color: "var(--text-secondary)", marginBottom: "4px" }}>{ticker}</p>
                          <p style={{ fontSize: "12px", lineHeight: "1.7" }}>{text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}