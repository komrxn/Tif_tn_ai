import api from './client'

export async function sendBroadcast(text: string, parseMode?: string): Promise<number> {
  const res = await api.post<{ queued: number }>('/broadcast', {
    text,
    parse_mode: parseMode || null,
  })
  return res.data.queued
}
