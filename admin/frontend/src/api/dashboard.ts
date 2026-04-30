import type { DashboardStats } from '../types'
import api from './client'

export async function getStats(): Promise<DashboardStats> {
  const res = await api.get<DashboardStats>('/dashboard/stats')
  return res.data
}
