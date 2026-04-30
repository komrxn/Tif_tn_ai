import type { ErrorPage } from '../types'
import api from './client'

export async function getErrors(params: {
  page?: number
  limit?: number
  handler?: string
}): Promise<ErrorPage> {
  const res = await api.get<ErrorPage>('/errors', { params })
  return res.data
}
