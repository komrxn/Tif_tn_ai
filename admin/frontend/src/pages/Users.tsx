import { useEffect, useState } from 'react'
import { getUsers } from '../api/users'
import BlockButton from '../components/BlockButton'
import DataTable, { type Column } from '../components/DataTable'
import type { User } from '../types'

type Filter = 'all' | 'active' | 'blocked'

export default function Users() {
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<{ total: number; items: User[] }>({ total: 0, items: [] })
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await getUsers({ page, limit: 50, search, filter })
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setPage(1)
  }, [filter, search])

  useEffect(() => {
    load()
  }, [filter, search, page])

  const handleToggle = (userId: string, newState: boolean) => {
    setData((prev) => ({
      ...prev,
      items: prev.items.map((u) => (u.id === userId ? { ...u, is_blocked: newState } : u)),
    }))
  }

  const columns: Column<User>[] = [
    { key: 'telegram_id', label: 'Telegram ID' },
    {
      key: 'username',
      label: 'Username',
      render: (u) => (u.username ? `@${u.username}` : '—'),
    },
    { key: 'language', label: 'Lang' },
    {
      key: 'is_blocked',
      label: 'Status',
      render: (u) => (u.is_blocked ? '🔴 Blocked' : '🟢 Active'),
    },
    {
      key: 'last_seen_at',
      label: 'Last seen',
      render: (u) => new Date(u.last_seen_at).toLocaleString(),
    },
    {
      key: 'action',
      label: 'Action',
      render: (u) => (
        <BlockButton
          userId={u.id}
          isBlocked={u.is_blocked}
          onToggle={(s) => handleToggle(u.id, s)}
        />
      ),
    },
  ]

  return (
    <div className="page">
      <h2>Users</h2>
      <div className="toolbar">
        <div className="tabs">
          {(['all', 'active', 'blocked'] as Filter[]).map((f) => (
            <button
              key={f}
              className={`tab ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <input
          className="search-input"
          placeholder="Search by ID or @username…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
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
    </div>
  )
}
