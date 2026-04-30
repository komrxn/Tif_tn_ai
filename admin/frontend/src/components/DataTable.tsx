import type { ReactNode } from 'react'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface Column<T = any> {
  key: string
  label: string
  render?: (row: T) => ReactNode
}

interface Props<T> {
  columns: Column<T>[]
  data: T[]
  total: number
  page: number
  limit: number
  onPageChange: (p: number) => void
  loading: boolean
  keyField?: keyof T
}

export default function DataTable<T extends { id: string }>({
  columns,
  data,
  total,
  page,
  limit,
  onPageChange,
  loading,
  keyField = 'id' as keyof T,
}: Props<T>) {
  const totalPages = Math.ceil(total / limit)

  return (
    <div className="table-wrap">
      {loading && <div className="table-loading">Loading…</div>}
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={String(row[keyField])}>
              {columns.map((c) => (
                <td key={c.key}>
                  {c.render
                    ? c.render(row)
                    : String((row as Record<string, unknown>)[c.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
          {data.length === 0 && !loading && (
            <tr>
              <td colSpan={columns.length} style={{ textAlign: 'center', color: '#888' }}>
                No data
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div className="pagination">
        <span>
          {total} total · page {page} of {totalPages || 1}
        </span>
        <div className="pagination-btns">
          <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
            ←
          </button>
          <button disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
            →
          </button>
        </div>
      </div>
    </div>
  )
}
