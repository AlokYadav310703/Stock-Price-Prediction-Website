import React, { useMemo, useState } from 'react'
import { AlertTriangle, Info, XCircle, CheckCircle2 } from 'lucide-react'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { PageHeader, Panel, LoadingState, ErrorState, EmptyState, Badge } from '../components/ui'

const SEVERITY_ICON = {
  INFO: Info,
  WARNING: AlertTriangle,
  CRITICAL: XCircle,
}
const SEVERITY_BADGE = {
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'critical',
}
const SEVERITY_ICON_COLOR = {
  INFO: 'text-signal-info',
  WARNING: 'text-signal-warn',
  CRITICAL: 'text-signal-down',
}

function timeAgo(iso) {
  const diffMs = Date.now() - new Date(iso).getTime()
  const days = Math.floor(diffMs / 86400000)
  if (days <= 0) return 'today'
  if (days === 1) return '1 day ago'
  return `${days} days ago`
}

export default function Alerts() {
  const { data, loading, error, reload } = useAsync(() => api.getAlerts(), [])
  const [severity, setSeverity] = useState('all')
  const [showResolved, setShowResolved] = useState(false)

  const filtered = useMemo(() => {
    if (!data) return []
    return data
      .filter((a) => showResolved || !a.resolved)
      .filter((a) => severity === 'all' || a.severity === severity)
  }, [data, severity, showResolved])

  if (loading) return <LoadingState label="Checking for alerts…" />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const counts = data
    ? { CRITICAL: data.filter((a) => a.severity === 'CRITICAL' && !a.resolved).length, WARNING: data.filter((a) => a.severity === 'WARNING' && !a.resolved).length, INFO: data.filter((a) => a.severity === 'INFO' && !a.resolved).length }
    : { CRITICAL: 0, WARNING: 0, INFO: 0 }

  return (
    <div>
      <PageHeader
        eyebrow="Alerts"
        title="Warnings & Model Health Alerts"
        description="Generated automatically when performance, data-quality, or drift thresholds are exceeded. Alerting can later route to email, Discord, or Slack."
        right={
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex gap-1 bg-ink-800 border border-ink-600 rounded-lg p-1">
              {['all', 'CRITICAL', 'WARNING', 'INFO'].map((s) => (
                <button
                  key={s}
                  onClick={() => setSeverity(s)}
                  className={`text-xs font-medium px-3 py-1.5 rounded-md transition-colors ${
                    severity === s ? 'bg-accent-dim text-paper border border-accent/40' : 'text-paper-dim hover:text-paper'
                  }`}
                >
                  {s === 'all' ? 'All' : s.charAt(0) + s.slice(1).toLowerCase()}
                </button>
              ))}
            </div>
            <label className="flex items-center gap-2 text-xs text-paper-dim cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                className="rounded border-ink-600 bg-ink-700 accent-accent"
              />
              Show resolved
            </label>
          </div>
        }
      />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <SeverityCount label="Critical" value={counts.CRITICAL} tone="critical" />
        <SeverityCount label="Warning" value={counts.WARNING} tone="warning" />
        <SeverityCount label="Info" value={counts.INFO} tone="info" />
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No alerts to show" message="Nothing matches the current filters, or the system has no active alerts." />
      ) : (
        <div className="space-y-3">
          {filtered.map((a) => {
            const Icon = SEVERITY_ICON[a.severity] || Info
            return (
              <Panel key={a.id} className="!p-4">
                <div className="flex items-start gap-3">
                  <Icon size={18} className={`mt-0.5 flex-shrink-0 ${SEVERITY_ICON_COLOR[a.severity]}`} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <Badge status={SEVERITY_BADGE[a.severity]}>{a.severity}</Badge>
                      <span className="text-[11px] text-paper-dim num uppercase tracking-wide">{a.alert_type}</span>
                      {a.resolved && (
                        <span className="inline-flex items-center gap-1 text-[11px] text-signal-up">
                          <CheckCircle2 size={12} /> Resolved
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-paper">{a.message}</p>
                    <p className="text-xs text-paper-dim num mt-1">{timeAgo(a.created_at)}</p>
                  </div>
                </div>
              </Panel>
            )
          })}
        </div>
      )}
    </div>
  )
}

function SeverityCount({ label, value, tone }) {
  const color = tone === 'critical' ? 'text-signal-down' : tone === 'warning' ? 'text-signal-warn' : 'text-signal-info'
  return (
    <div className="panel p-4 text-center">
      <div className={`num text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-paper-dim mt-1">{label} (active)</div>
    </div>
  )
}
