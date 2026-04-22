// src/hooks/useSession.js
import { useState, useEffect } from "react"

function generateUUID() {
  return crypto.randomUUID()
}

export function useSession() {
  const [sessionKey, setSessionKey] = useState(null)

  useEffect(() => {
    let key = localStorage.getItem("paper_market_session")
    if (!key) {
      key = generateUUID()
      localStorage.setItem("paper_market_session", key)
    }
    setSessionKey(key)
  }, [])

  return sessionKey
}