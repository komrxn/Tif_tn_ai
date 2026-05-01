import { useEffect, useState } from 'react'
import { getRequest, getRequests } from '../api/requests'
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

const TYPE_ICONS: Record<string, string> = {
  text: '💬',
  photo: '🖼',
  voice: '🎤',
}

interface Props {
  defaultType?: RequestType
}

function RequestDrawer({
  id,
  onClose,
}: {
  id: string
  onClose: () => void
}) {
  const [detail, setDetail] = useState<Request | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setDetail(null)
    getRequest(id)
      .then(setDetail)
      .finally(() => setLoading(false))
  }, [id])

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div className="drawer-header">
          <h3>Request Detail</h3>
          <button className="drawer-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="drawer-body">
          {loading && <div className="page-loading">Loading…</div>}
          {!loading && !detail && <div className="page-loading">Not found</div>}
          {detail && (
            <>
              <div className="detail-field">
                <span className="detail-label">User Input</span>
                <div className="detail-value">{detail.query_text}</div>
              </div>

              <div className="detail-row">
                <div className="detail-field">
                  <span className="detail-label">Type</span>
                  <div className="detail-value">
                    {TYPE_ICONS[detail.query_type] ?? ''} {detail.query_type}
                  </div>
                </div>
                <div className="detail-field">
                  <span className="detail-label">Time</span>
                  <div className="detail-value">
                    {new Date(detail.created_at).toLocaleString()}
                  </div>
                </div>
              </div>

              <hr className="detail-divider" />

              {detail.result_code ? (
                <>
                  <div className="detail-field">
                    <span className="detail-label">Result Code</span>
                    <div className="detail-value mono">{detail.result_code}</div>
                  </div>
                  <div className="detail-field">
                    <span className="detail-label">Result Name</span>
                    <div className="detail-value">{detail.result_name ?? '—'}</div>
                  </div>
                  <div className="detail-row">
                    <div className="detail-field">
                      <span className="detail-label">Confidence</span>
                      <div className="detail-value">
                        <ConfidenceBadge value={detail.confidence} />
                        {detail.confidence != null && (
                          <span style={{ marginLeft: 8, color: 'var(--text-muted)', fontSize: 12 }}>
                            ({(detail.confidence * 100).toFixed(1)}%)
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="detail-field">
                      <span className="detail-label">Response time</span>
                      <div className="detail-value">{detail.response_time_ms} ms</div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="detail-field">
                  <span className="detail-label">Result</span>
                  <div className="detail-value" style={{ color: 'var(--danger)' }}>
                    Classification failed — no code returned
                  </div>
                </div>
              )}

              <hr className="detail-divider" />

              <div className="detail-row">
                <div className="detail-field">
                  <span className="detail-label">Tokens (prompt)</span>
                  <div className="detail-value">
                    {detail.tokens_prompt != null ? detail.tokens_prompt.toLocaleString() : '—'}
                  </div>
                </div>
                <div className="detail-field">
                  <span className="detail-label">Tokens (completion)</span>
                  <div className="detail-value">
                    {detail.tokens_completion != null
                      ? detail.tokens_completion.toLocaleString()
                      : '—'}
                  </div>
                </div>
              </div>

              {detail.audio_seconds != null && (
                <div className="detail-field">
                  <span className="detail-label">Audio duration</span>
                  <div className="detail-value">{detail.audio_seconds.toFixed(1)} s</div>
                </div>
              )}

              <hr className="detail-divider" />

              <div className="detail-row">
                <div className="detail-field">
                  <span className="detail-label">Telegram ID</span>
                  <div className="detail-value mono">
                    {detail.telegram_id ?? '—'}
                  </div>
                </div>
                <div className="detail-field">
                  <span className="detail-label">Username</span>
                  <div className="detail-value">
                    {detail.username ? `@${detail.username}` : '—'}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}

export default function Requests({ defaultType = 'all' }: Props) {
  const [page, setPage] = useState(1)
  const [data, setData] = useState<{ total: number; items: Request[] }>({ total: 0, items: [] })
  const [loading, setLoading] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

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
    {
      key: 'query_type',
      label: 'Type',
      render: (r) => `${TYPE_ICONS[r.query_type] ?? ''} ${r.query_type}`,
    },
    {
      key: 'query_text',
      label: 'Query',
      render: (r) => (
        <span className="query-text" title={r.query_text}>
          {r.query_text.slice(0, 60) + (r.query_text.length > 60 ? '…' : '')}
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
      label: 'ms',
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
        onRowClick={(r) => setSelectedId(r.id)}
        rowClassName={() => 'row-clickable'}
      />
      {selectedId && (
        <RequestDrawer id={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  )
}
