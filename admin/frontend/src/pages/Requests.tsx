import { useEffect, useState } from 'react'
import { getRequests } from '../api/requests'
import ConfidenceBadge from '../components/ConfidenceBadge'
import DataTable, { type Column } from '../components/DataTable'
import type { Request } from '../types'

type RequestType = 'all' | 'text' | 'photo' | 'voice' | 'low_confidence' | 'failed'

const TYPE_LABELS: Record<RequestType, string> = {
  all: 'All',
  text: 'Text',
  photo: 'Photo',
  voice: 'Voice',
  low_confidence: 'Low Confidence',
  failed: 'Failed',
}

interface Props {
  defaultType?: RequestType
}

export default function Requests({ defaultType = 'all' }: Props) {
  const [page, setPage] = useState(1)
  const [data, setData] = useState<{ total: number; items: Request[] }>({ total: 0, items: [] })
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    setPage(1)
  }, [defaultType])

  useEffect(() => {
    setLoading(true)
    getRequests({ page, limit: 50, type: defaultType })
      .then(setData)
      .finally(() => setLoading(false))
  }, [defaultType, page])

  const columns: Column<Request>[] = [
    {
      key: 'created_at',
      label: 'Time',
      render: (r) => new Date(r.created_at).toLocaleString(),
    },
    {
      key: 'user',
      label: 'User',
      render: (r) =>
        r.telegram_id ? (
          <span>
            {r.telegram_id}
            {r.username && ` @${r.username}`}
          </span>
        ) : (
          '—'
        ),
    },
    { key: 'query_type', label: 'Type' },
    {
      key: 'query_text',
      label: 'Query',
      render: (r) => (
        <span
          className="query-text"
          title={r.query_text}
          onClick={() => setExpanded(expanded === r.id ? null : r.id)}
          style={{ cursor: 'pointer' }}
        >
          {expanded === r.id
            ? r.query_text
            : r.query_text.slice(0, 60) + (r.query_text.length > 60 ? '…' : '')}
        </span>
      ),
    },
    { key: 'result_code', label: 'Code', render: (r) => r.result_code || '—' },
    {
      key: 'confidence',
      label: 'Confidence',
      render: (r) => <ConfidenceBadge value={r.confidence} />,
    },
    {
      key: 'response_time_ms',
      label: 'Time (ms)',
      render: (r) => String(r.response_time_ms),
    },
    {
      key: 'tokens',
      label: 'Tokens',
      render: (r) =>
        r.tokens_prompt != null ? `${r.tokens_prompt}↑ ${r.tokens_completion}↓` : '—',
    },
  ]

  return (
    <div className="page">
      <h2>Requests — {TYPE_LABELS[defaultType]}</h2>
      <DataTable
        columns={columns}
        data={data.items}
        total={data.total}
        page={page}
        limit={50}
        onPageChange={setPage}
        loading={loading}
      />
    </div>
  )
}
