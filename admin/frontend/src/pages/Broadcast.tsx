import type { FormEvent } from 'react'
import { useState } from 'react'
import { sendBroadcast } from '../api/broadcast'

export default function Broadcast() {
  const [text, setText] = useState('')
  const [parseMode, setParseMode] = useState('')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    if (!confirm(`Send this message to ALL non-blocked users?`)) return

    setLoading(true)
    setToast(null)
    setError(null)
    try {
      const queued = await sendBroadcast(text, parseMode || undefined)
      setToast(`Broadcast queued for ${queued} users`)
      setText('')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to send broadcast'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h2>Broadcast</h2>
      <p className="text-muted">Send a message to all non-blocked users via Telegram.</p>

      {toast && <div className="toast toast-success">{toast}</div>}
      {error && <div className="toast toast-error">{error}</div>}

      <form className="broadcast-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>Parse Mode</label>
          <select value={parseMode} onChange={(e) => setParseMode(e.target.value)}>
            <option value="">Plain text</option>
            <option value="HTML">HTML</option>
            <option value="Markdown">Markdown</option>
          </select>
        </div>
        <div className="form-row">
          <label>Message</label>
          <textarea
            rows={8}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter your message…"
            required
          />
        </div>
        <button type="submit" disabled={loading || !text.trim()}>
          {loading ? 'Sending…' : 'Send Broadcast'}
        </button>
      </form>
    </div>
  )
}
