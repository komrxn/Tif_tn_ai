import { useEffect, useState } from 'react'
import { getStats } from '../api/dashboard'
import { getTraffic } from '../api/usage'
import StatCard from '../components/StatCard'
import TrafficChart from '../components/TrafficChart'
import type { DashboardStats, TrafficPoint } from '../types'

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [traffic, setTraffic] = useState<TrafficPoint[]>([])

  useEffect(() => {
    getStats().then(setStats)
    getTraffic(7).then(setTraffic)
  }, [])

  if (!stats) return <div className="page-loading">Loading…</div>

  const typeTotal = Object.values(stats.queries_by_type).reduce((a, b) => a + b, 0)

  return (
    <div className="page">
      <h2>Dashboard</h2>
      <div className="stat-grid">
        <StatCard label="Total Users" value={stats.total_users} />
        <StatCard label="Blocked Users" value={stats.blocked_users} />
        <StatCard label="Queries Today" value={stats.total_queries_today} />
        <StatCard label="All Queries" value={stats.total_queries_all} />
        <StatCard label="Avg Response" value={`${stats.avg_response_ms} ms`} />
        <StatCard label="Errors Today" value={stats.errors_today} />
        <StatCard
          label="Low Confidence (7d)"
          value={stats.low_confidence_count}
          sub="confidence < 70%"
        />
        <StatCard label="Failed (7d)" value={stats.failed_count} sub="no result" />
      </div>

      <div className="section">
        <h3>Query types (all time)</h3>
        <div className="type-badges">
          {Object.entries(stats.queries_by_type).map(([type, cnt]) => (
            <span key={type} className="type-badge">
              {type}: <strong>{cnt}</strong>
              {typeTotal > 0 && ` (${Math.round((cnt / typeTotal) * 100)}%)`}
            </span>
          ))}
        </div>
      </div>

      <div className="section">
        <h3>Traffic — last 7 days</h3>
        <TrafficChart data={traffic} />
      </div>
    </div>
  )
}
