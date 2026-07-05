interface ScoreBarProps {
  label: string
  value: number  // 0–100 or 0–1 (will be normalized to 0-100)
  max?: number
  variant?: 'primary' | 'contradiction'
}

export function ScoreBar({ label, value, max = 100, variant = 'primary' }: ScoreBarProps) {
  const pct = Math.min(100, Math.round((value / max) * 100))
  const color = variant === 'contradiction' ? 'var(--signal-red)' : 'var(--accent-amber)'

  return (
    <div className="mb-2">
      <div className="flex items-center justify-between mb-0.5">
        <span
          className="font-stamp text-xs"
          style={{ color: 'var(--text-muted)', fontSize: '0.6rem', letterSpacing: '0.08em' }}
        >
          {label}
        </span>
        <span
          className="font-stamp text-xs"
          style={{ color, fontSize: '0.6rem' }}
        >
          {variant === 'contradiction' ? value : `${pct}%`}
        </span>
      </div>
      <div
        className="h-0.5 w-full"
        style={{ backgroundColor: 'var(--divider)' }}
      >
        <div
          className="h-full transition-all duration-700"
          style={{
            width: variant === 'contradiction' ? `${Math.min(100, value * 20)}%` : `${pct}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  )
}
