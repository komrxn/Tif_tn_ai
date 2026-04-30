import type { UserPage } from '../types'
import api from './client'

export async function getUsers(params: {
  page?: number
  limit?: number
  search?: string
  filter?: string
}): Promise<UserPage> {
  const res = await api.get<UserPage>('/users', { params })
  return res.data
}

export async function setUserBlocked(userId: string, isBlocked: boolean): Promise<void> {
  await api.patch(`/users/${userId}/block`, { is_blocked: isBlocked })
}
