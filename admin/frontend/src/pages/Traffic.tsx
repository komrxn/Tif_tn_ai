import { useEffect, useState } from 'react'
import { getTraffic } from '../api/usage'
import TrafficChart from '../components/TrafficChart'
import type { TrafficPoint } from '../types'

export default function Traffic() {
  const [days, setDays] = useState(30)
  const [data, setData] = useState<TrafficPoint[]>([])

  useEffect(() => {
    getTraffic(days).then(setData)
  }, [days])

  const total = data.reduce((s, d) => s + d.count, 0)

  return (
    <div className="page">
      <h2>Traffic</h2>
      <div className="toolbar">
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
        <span className="stat-inline">{total} total requests</span>
      </div>
      <TrafficChart data={data} />
    </div>
  )
}
