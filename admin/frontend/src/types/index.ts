export interface User {
  id: string
  telegram_id: number
  username: string | null
  language: string
  is_blocked: boolean
  last_seen_at: string
  created_at: string
}

export interface UserPage {
  total: number
  items: User[]
}

export interface Request {
  id: string
  user_id: string
  telegram_id: number | null
  username: string | null
  query_text: string
  query_type: string
  result_code: string | null
  result_name: string | null
  confidence: number | null
  response_time_ms: number
  tokens_prompt: number | null
  tokens_completion: number | null
  audio_seconds: number | null
  created_at: string
}

export interface RequestPage {
  total: number
  items: Request[]
}

export interface DashboardStats {
  total_users: number
  blocked_users: number
  total_queries_today: number
  total_queries_all: number
  avg_response_ms: number
  queries_by_type: Record<string, number>
  low_confidence_count: number
  failed_count: number
  errors_today: number
}

export interface TrafficPoint {
  date: string
  count: number
}

export interface CostBreakdown {
  gpt51_input_usd: number
  gpt51_output_usd: number
  whisper_usd: number
  total_usd: number
}

export interface CostResponse {
  total_usd: number
  breakdown: CostBreakdown
  by_day: { date: string; total_usd: number }[]
}

export interface ErrorEntry {
  id: string
  user_id: string | null
  telegram_id: number | null
  handler: string
  error_type: string
  message: string
  traceback: string | null
  query_type: string | null
  created_at: string
}

export interface ErrorPage {
  total: number
  items: ErrorEntry[]
}
