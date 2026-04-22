// src/components/Navbar.jsx
import { useState, useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"

export default function Navbar() {
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light")
  const [search, setSearch] = useState("")
  const [exchange, setExchange] = useState("US")
  const navigate = useNavigate()

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme)
    localStorage.setItem("theme", theme)
  }, [theme])

  function handleSearch(e) {
    e.preventDefault()
    if (!search.trim()) return
    navigate(`/ticker/${search.toUpperCase()}?exchange=${exchange}`)
    setSearch("")
  }

  return (
    <nav style={{
      borderBottom: "1px solid var(--border)",
      padding: "12px 24px",
      display: "flex",
      alignItems: "center",
      gap: "24px",
      background: "var(--surface)"
    }}>
      <Link to="/" style={{ color: "var(--text-primary)", textDecoration: "none", fontWeight: "bold", letterSpacing: "0.05em" }}>
        PAPER MARKET
      </Link>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: "8px", flex: 1, maxWidth: "400px" }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="ticker (AAPL, RELIANCE...)"
          style={{ flex: 1 }}
        />
        <select value={exchange} onChange={e => setExchange(e.target.value)} style={{ width: "80px" }}>
          <option value="US">US</option>
          <option value="NSE">NSE</option>
          <option value="BSE">BSE</option>
        </select>
        <button type="submit" className="btn">GO</button>
      </form>

      <div style={{ marginLeft: "auto", display: "flex", gap: "16px", alignItems: "center" }}>
        <Link to="/" className="muted" style={{ textDecoration: "none", fontSize: "13px" }}>dashboard</Link>
        <button
          className="btn outline"
          onClick={() => setTheme(t => t === "light" ? "dark" : "light")}
          style={{ padding: "4px 12px" }}
        >
          {theme === "light" ? "dark" : "light"}
        </button>
      </div>
    </nav>
  )
}