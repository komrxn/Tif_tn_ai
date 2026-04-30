import { useState } from 'react'
import { setUserBlocked } from '../api/users'

interface Props {
  userId: string
  isBlocked: boolean
  onToggle: (newState: boolean) => void
}

export default function BlockButton({ userId, isBlocked, onToggle }: Props) {
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    const action = isBlocked ? 'unblock' : 'block'
    if (!confirm(`Are you sure you want to ${action} this user?`)) return
    setLoading(true)
    try {
      await setUserBlocked(userId, !isBlocked)
      onToggle(!isBlocked)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      className={`btn-sm ${isBlocked ? 'btn-success' : 'btn-danger'}`}
      onClick={handleClick}
      disabled={loading}
    >
      {loading ? '...' : isBlocked ? 'Unblock' : 'Block'}
    </button>
  )
}
