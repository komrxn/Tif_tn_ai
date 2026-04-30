import clsx from 'clsx'

interface Props {
  value: number | null
}

export default function ConfidenceBadge({ value }: Props) {
  if (value === null) return <span className="badge badge-gray">—</span>
  const pct = Math.round(value * 100)
  const cls = value >= 0.85 ? 'badge-green' : value >= 0.7 ? 'badge-yellow' : 'badge-red'
  return <span className={clsx('badge', cls)}>{pct}%</span>
}
