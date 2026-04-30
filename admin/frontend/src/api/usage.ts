import type { CostResponse, TrafficPoint } from '../types'
import api from './client'

export async function getTraffic(days = 30): Promise<TrafficPoint[]> {
  const res = await api.get<{ data: TrafficPoint[] }>('/usage/traffic', { params: { days } })
  return res.data.data
}

export async function getCosts(days = 30): Promise<CostResponse> {
  const res = await api.get<CostResponse>('/usage/costs', { params: { days } })
  return res.data
}
