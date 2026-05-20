// src/api.js
import axios from "axios"

const BASE_URL = "http://localhost:8000"

function client(sessionKey) {
  return axios.create({
    baseURL: BASE_URL,
    headers: sessionKey ? { "X-Session-Key": sessionKey } : {},
  })
}

export async function fetchHistory(ticker, exchange = "US", period = "3mo", sessionKey) {
  const res = await client(sessionKey).get("/market/history", {
    params: { ticker, exchange, period },
  })
  return res.data
}

export async function fetchQuote(ticker, exchange = "US", sessionKey) {
  const res = await client(sessionKey).get("/market/quote", {
    params: { ticker, exchange },
  })
  return res.data
}

export async function fetchIndices(sessionKey) {
  const res = await client(sessionKey).get("/agent/indices")
  return res.data
}

export async function fetchPortfolio(sessionKey, market = "US") {
  const res = await client(sessionKey).get("/portfolio/", { params: { market } })
  return res.data
}

export async function placeOrder(order, sessionKey) {
  const res = await client(sessionKey).post("/portfolio/order", order)
  return res.data
}

export async function fetchOrders(sessionKey, market = "US") {
  const res = await client(sessionKey).get("/portfolio/orders", { params: { market } })
  return res.data
}

export async function fetchSentiment(ticker, sessionKey) {
  const res = await client(sessionKey).get(`/sentiment/summary/${ticker}`)
  return res.data
}

export async function triggerScrape(ticker, sessionKey) {
  const res = await client(sessionKey).post(`/sentiment/scrape/${ticker}`)
  return res.data
}

export async function fetchAnalysis(ticker, exchange = "US", forceRefresh = false, sessionKey) {
  const res = await client(sessionKey).get(`/agent/analyse/${ticker}`, {
    params: { exchange, force_refresh: forceRefresh },
  })
  return res.data
}

export async function fetchMarketNews(sessionKey) {
  const res = await client(sessionKey).get("/agent/news")
  return res.data
}

export async function fetchComparisons(sessionKey) {
  const res = await client(sessionKey).get("/compare/suggestions")
  return res.data
}

export async function fetchCompare(tickerA, exchangeA, tickerB, exchangeB, period, sessionKey) {
  const res = await client(sessionKey).get("/compare/", {
    params: { ticker_a: tickerA, exchange_a: exchangeA, ticker_b: tickerB, exchange_b: exchangeB, period }
  })
  return res.data
}

export async function fetchTickerNews(ticker, exchange = "US", sessionKey) {
  const res = await client(sessionKey).get("/market/news", { params: { ticker, exchange } })
  return res.data
}

export async function fetchPriceTargets(ticker, exchange = "US", sessionKey) {
  const res = await client(sessionKey).get("/market/price-targets", { params: { ticker, exchange } })
  return res.data
}

export async function fetchUpgradesDowngrades(ticker, exchange = "US", sessionKey) {
  const res = await client(sessionKey).get("/market/upgrades-downgrades", { params: { ticker, exchange } })
  return res.data
}

export async function fetchRecommendations(ticker, exchange = "US", sessionKey) {
  const res = await client(sessionKey).get("/market/recommendations", { params: { ticker, exchange } })
  return res.data
}

export async function fetchScreener(preset = "most_active") {
  const res = await client(null).get(`/screener/${preset}`)
  return res.data
}