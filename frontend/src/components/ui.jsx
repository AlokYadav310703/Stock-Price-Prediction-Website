import React from 'react'

export function PageHeader({ eyebrow, title, description, right }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-6">
      <div>
        {eyebrow && (
          <div className="text-xs font-semibold tracking-widest uppercase text-signal-info mb-1">
            {eyebrow}
          </div>
        )}
        <h1 className="text-2xl font-bold text-paper">{title}</h1>
        {description && <p className="text-sm text-paper-dim mt-1 max-w-2xl">{description}</p>}
      </div>
      {right && <div className="flex-shrink-0">{right}</div>}
    </div>
  )
}

export function Panel({ title, subtitle, actions, className = '', children }) {
  return (
    <div className={`panel p-5 ${className}`}>
      {(title || actions) && (
        <div className="flex items-start justify-between mb-4 gap-3">
          <div>
            {title && <h2 className="text-sm font-semibold text-paper">{title}</h2>}
            {subtitle && <p className="text-xs text-paper-dim mt-0.5">{subtitle}</p>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </div>
  )
}

export function MetricCard({ label, value, delta, deltaGood, suffix, hint }) {
  const deltaColor =
    delta == null
      ? 'text-paper-dim'
      : deltaGood === false
      ? 'text-signal-down'
      : deltaGood === true
      ? 'text-signal-up'
      : delta > 0
      ? 'text-signal-up'
      : delta < 0
      ? 'text-signal-down'
      : 'text-paper-dim'

  return (
    <div className="panel p-4">
      <div className="text-xs uppercase tracking-wide text-paper-dim mb-2">{label}</div>
      <div className="flex items-baseline gap-2 flex-wrap">
        <span className="num text-2xl font-semibold text-paper">{value}</span>
        {suffix && <span className="text-xs text-paper-dim">{suffix}</span>}
      </div>
      {delta != null && (
        <div className={`num text-xs mt-1 font-medium ${deltaColor}`}>
          {delta > 0 ? '▲' : delta < 0 ? '▼' : '—'} {delta}
        </div>
      )}
      {hint && <div className="text-xs text-paper-dim mt-1">{hint}</div>}
    </div>
  )
}

const BADGE_STYLES = {
  ok: 'bg-signal-up/10 text-signal-up border-signal-up/30',
  normal: 'bg-signal-up/10 text-signal-up border-signal-up/30',
  healthy: 'bg-signal-up/10 text-signal-up border-signal-up/30',
  correct: 'bg-signal-up/10 text-signal-up border-signal-up/30',
  warning: 'bg-signal-warn/10 text-signal-warn border-signal-warn/30',
  incorrect: 'bg-signal-down/10 text-signal-down border-signal-down/30',
  high_drift: 'bg-signal-down/10 text-signal-down border-signal-down/30',
  critical: 'bg-signal-down/10 text-signal-down border-signal-down/30',
  info: 'bg-signal-info/10 text-signal-info border-signal-info/30',
  neutral: 'bg-ink-600 text-paper-dim border-ink-600',
}

export function Badge({ status = 'neutral', children }) {
  const style = BADGE_STYLES[status] || BADGE_STYLES.neutral
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}>
      {children}
    </span>
  )
}

export function DirectionTag({ direction }) {
  if (direction === 'UP') return <span className="num text-signal-up font-semibold">▲ UP</span>
  if (direction === 'DOWN') return <span className="num text-signal-down font-semibold">▼ DOWN</span>
  return <span className="num text-paper-dim font-semibold">— FLAT</span>
}

export function ResultTag({ isCorrect }) {
  if (isCorrect === null || isCorrect === undefined) return <Badge status="neutral">Pending</Badge>
  return isCorrect ? <Badge status="correct">✓ Correct</Badge> : <Badge status="incorrect">✗ Incorrect</Badge>
}

export function LoadingState({ label = 'Loading data…' }) {
  return (
    <div className="panel p-8 flex flex-col items-center justify-center text-center gap-3">
      <div className="h-8 w-8 rounded-full border-2 border-ink-600 border-t-signal-info animate-spin" />
      <p className="text-sm text-paper-dim">{label}</p>
    </div>
  )
}

export function ErrorState({ message = 'Something went wrong.', onRetry }) {
  return (
    <div className="panel p-8 flex flex-col items-center justify-center text-center gap-3 border-signal-down/30">
      <div className="text-signal-down text-2xl">⚠</div>
      <p className="text-sm text-paper">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 text-xs font-medium px-3 py-1.5 rounded-md bg-ink-600 hover:bg-ink-700 text-paper transition-colors"
        >
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title = 'Nothing here yet', message = 'Insufficient data.' }) {
  return (
    <div className="panel p-8 flex flex-col items-center justify-center text-center gap-2">
      <div className="text-paper-dim text-2xl">◌</div>
      <p className="text-sm font-medium text-paper">{title}</p>
      <p className="text-xs text-paper-dim max-w-sm">{message}</p>
    </div>
  )
}

export function fmtUSD(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })}`
}

export function fmtPct(n, digits = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return `${n > 0 ? '+' : ''}${Number(n).toFixed(digits)}%`
}
