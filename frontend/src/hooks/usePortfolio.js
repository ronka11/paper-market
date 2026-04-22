// src/hooks/usePortfolio.js
import { useState, useEffect } from "react"
import { fetchPortfolio } from "../api"

export function usePortfolio(sessionKey) {
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)

  async function reload() {
    if (!sessionKey) return
    setLoading(true)
    try {
      const data = await fetchPortfolio(sessionKey)
      setPortfolio(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, [sessionKey])

  return { portfolio, loading, reload }
}