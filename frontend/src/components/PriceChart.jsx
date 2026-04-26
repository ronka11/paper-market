// src/components/PriceChart.jsx
import { useEffect, useRef } from "react"
import { createChart, CandlestickSeries, AreaSeries } from "lightweight-charts"

export default function PriceChart({ data = [], height = 200, mode = "area" }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!data.length || !containerRef.current) return

    const isDark = document.documentElement.getAttribute("data-theme") === "dark"

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { color: "transparent" },
        textColor: isDark ? "#888878" : "#5a5a52",
        fontFamily: "Courier New, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: isDark ? "#2a2a26" : "#e0e0d8" },
        horzLines: { color: isDark ? "#2a2a26" : "#e0e0d8" },
      },
      rightPriceScale: {
        borderColor: isDark ? "#2a2a26" : "#ccccc4",
        autoScale: true,
      },
      timeScale: {
        borderColor: isDark ? "#2a2a26" : "#ccccc4",
        timeVisible: true,
      },
      crosshair: { mode: 1 },
    })

    const isUp = data[data.length - 1]?.close >= data[0]?.close

    if (mode === "candle") {
      const series = chart.addSeries(CandlestickSeries, {
        upColor: "#4caf50",
        downColor: "#e57373",
        borderUpColor: "#4caf50",
        borderDownColor: "#e57373",
        wickUpColor: "#4caf50",
        wickDownColor: "#e57373",
      })
      series.setData(data.map(d => ({
        time: d.date.slice(0, 10),
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      })))
    } else {
      const color = isUp ? "#4caf50" : "#e57373"
      const series = chart.addSeries(AreaSeries, {
        lineColor: color,
        topColor: color + "33",
        bottomColor: color + "00",
        lineWidth: 1.5,
        priceScaleId: "right",
      })
      series.setData(data.map(d => ({
        time: d.date.slice(0, 10),
        value: d.close,
      })))
    }

    chart.timeScale().fitContent()
    chartRef.current = chart

    return () => { chart.remove(); chartRef.current = null }
  }, [data, height, mode])

  if (!data.length) return (
    <p className="muted" style={{ padding: "40px 0", textAlign: "center" }}>no data</p>
  )

  return <div ref={containerRef} style={{ width: "100%" }} />
}