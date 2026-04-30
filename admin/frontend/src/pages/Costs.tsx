import { useEffect, useState } from 'react'
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { getCosts } from '../api/usage'
import type { CostResponse } from '../types'

const COLORS = ['#6366f1', '#22d3ee', '#f59e0b']

export default function Costs() {
  const [days, setDays] = useState(30)
  const [data, setData] = useState<CostResponse | null>(null)

  useEffect(() => {
    getCosts(days).then(setData)
  }, [days])

  if (!data) return <div className="page-loading">Loading…</div>

  const pieData = [
    { name: 'GPT-5.1 Input', value: data.breakdown.gpt51_input_usd },
    { name: 'GPT-5.1 Output', value: data.breakdown.gpt51_output_usd },
    { name: 'Whisper', value: data.breakdown.whisper_usd },
  ].filter((d) => d.value > 0)

  return (
    <div className="page">
      <h2>Costs</h2>
      <div className="toolbar">
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
        <span className="stat-inline">
          Total: <strong>${data.total_usd.toFixed(4)}</strong>
        </span>
      </div>

      <div className="cost-layout">
        <div className="cost-pie">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90}>
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => (typeof v === 'number' ? `$${v.toFixed(6)}` : v)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="cost-breakdown">
          <table className="data-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Cost (USD)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>GPT-5.1 Input</td>
                <td>${data.breakdown.gpt51_input_usd.toFixed(6)}</td>
              </tr>
              <tr>
                <td>GPT-5.1 Output</td>
                <td>${data.breakdown.gpt51_output_usd.toFixed(6)}</td>
              </tr>
              <tr>
                <td>Whisper</td>
                <td>${data.breakdown.whisper_usd.toFixed(6)}</td>
              </tr>
              <tr style={{ fontWeight: 'bold' }}>
                <td>Total</td>
                <td>${data.total_usd.toFixed(6)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <h3>By day</h3>
      <table className="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Cost (USD)</th>
          </tr>
        </thead>
        <tbody>
          {data.by_day.map((d) => (
            <tr key={d.date}>
              <td>{d.date}</td>
              <td>${d.total_usd.toFixed(6)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
