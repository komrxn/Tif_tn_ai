import type { RequestPage } from '../types'
import api from './client'

export async function getRequests(params: {
  page?: number
  limit?: number
  type?: string
}): Promise<RequestPage> {
  const res = await api.get<RequestPage>('/requests', { params })
  return res.data
}
