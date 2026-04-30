import { useEffect, useState } from 'react'
import { getErrors } from '../api/errors'
import DataTable, { type Column } from '../components/DataTable'
import type { ErrorEntry } from '../types'

export default function Errors() {
  const [page, setPage] = useState(1)
  const [handler, setHandler] = useState('')
  const [data, setData] = useState<{ total: number; items: ErrorEntry[] }>({
    total: 0,
    items: [],
  })
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    setPage(1)
  }, [handler])

  useEffect(() => {
    setLoading(true)
    getErrors({ page, limit: 50, handler })
      .then(setData)
      .finally(() => setLoading(false))
  }, [page, handler])

  const columns: Column<ErrorEntry>[] = [
    {
      key: 'created_at',
      label: 'Time',
      render: (e) => new Date(e.created_at).toLocaleString(),
    },
    { key: 'handler', label: 'Handler' },
    { key: 'error_type', label: 'Type' },
    {
      key: 'message',
      label: 'Message',
      render: (e) => (
        <span title={e.message}>
          {e.message.slice(0, 80)}
          {e.message.length > 80 ? '…' : ''}
        </span>
      ),
    },
    {
      key: 'user',
      label: 'User',
      render: (e) => (e.telegram_id ? String(e.telegram_id) : '—'),
    },
    {
      key: 'traceback',
      label: 'Traceback',
      render: (e) =>
        e.traceback ? (
          <span
            className="link"
            onClick={() => setExpanded(expanded === e.id ? null : e.id)}
            style={{ cursor: 'pointer' }}
          >
            {expanded === e.id ? 'hide' : 'show'}
          </span>
        ) : (
          '—'
        ),
    },
  ]

  return (
    <div className="page">
      <h2>Errors</h2>
      <div className="toolbar">
        <select value={handler} onChange={(e) => setHandler(e.target.value)}>
          <option value="">All handlers</option>
          <option value="query">query</option>
          <option value="photo">photo</option>
          <option value="voice">voice</option>
          <option value="unhandled">unhandled</option>
        </select>
      </div>
      <DataTable
        columns={columns}
        data={data.items}
        total={data.total}
        page={page}
        limit={50}
        onPageChange={setPage}
        loading={loading}
      />
      {expanded && (
        <div className="traceback-panel">
          <button onClick={() => setExpanded(null)} className="btn-sm btn-danger">
            Close
          </button>
          <pre>{data.items.find((e) => e.id === expanded)?.traceback}</pre>
        </div>
      )}
    </div>
  )
}
