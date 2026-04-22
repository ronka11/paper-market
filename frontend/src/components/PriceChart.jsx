// src/components/PriceChart.jsx
import {
  ResponsiveContainer, AreaChart, Area,
  XAxis, YAxis, Tooltip, CartesianGrid
} from "recharts"

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" })
}

function formatPrice(val) {
  if (val >= 1000) return val.toLocaleString("en-IN", { maximumFractionDigits: 0 })
  return val.toFixed(2)
}

export default function PriceChart({ data = [], height = 200, color = "#2a2a2a" }) {
  if (!data.length) return <p className="muted" style={{ padding: "40px 0", textAlign: "center" }}>no data</p>

  const isUp = data[data.length - 1]?.close >= data[0]?.close
  const lineColor = isUp ? "var(--green)" : "var(--red)"
  const usedColor = color === "auto" ? lineColor : color

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 8 }}>
        <defs>
          <linearGradient id={`grad-${usedColor}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={usedColor} stopOpacity={0.15} />
            <stop offset="95%" stopColor={usedColor} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: "var(--text-secondary)", fontFamily: "var(--font)" }}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={formatPrice}
          tick={{ fontSize: 11, fill: "var(--text-secondary)", fontFamily: "var(--font)" }}
          tickLine={false}
          axisLine={false}
          width={60}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            fontFamily: "var(--font)",
            fontSize: "12px",
          }}
          labelFormatter={formatDate}
          formatter={(val) => [formatPrice(val), "close"]}
        />
        <Area
          type="monotone"
          dataKey="close"
          stroke={usedColor}
          strokeWidth={1.5}
          fill={`url(#grad-${usedColor})`}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}