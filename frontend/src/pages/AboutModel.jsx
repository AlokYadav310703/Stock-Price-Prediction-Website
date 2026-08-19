import React from 'react'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { PageHeader, Panel, LoadingState, ErrorState, Badge } from '../components/ui'

export default function AboutModel() {
  const { data, loading, error, reload } = useAsync(() => api.getAboutModel(), [])

  if (loading) return <LoadingState label="Loading model documentation…" />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const m = data

  return (
    <div>
      <PageHeader
        eyebrow={`Model ${m.version}`}
        title={m.name}
        description="How the prediction pipeline is built, what it's trained on, and where it falls short."
      />

      <Panel title="Architecture" subtitle="Two-stage pipeline">
        <div className="space-y-4">
          {m.architecture.map((s, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex-shrink-0 h-7 w-7 rounded-full bg-accent-dim border border-accent/40 text-signal-info text-xs font-semibold flex items-center justify-center num">
                {i + 1}
              </div>
              <div>
                <div className="text-sm font-semibold text-paper">{s.stage}</div>
                <p className="text-sm text-paper-dim mt-1">{s.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <Panel title="Input Features">
          <ul className="space-y-2">
            {m.features.map((f, i) => (
              <li key={i} className="text-sm text-paper flex items-start gap-2">
                <span className="text-signal-info mt-1">•</span>
                {f}
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Training &amp; Methodology">
          <div className="mb-3">
            <span className="text-xs text-paper-dim">Training period</span>
            <div className="text-sm text-paper num mt-0.5">{m.training_period}</div>
          </div>
          <div>
            <span className="text-xs text-paper-dim">Prediction methodology</span>
            <p className="text-sm text-paper mt-1">{m.prediction_methodology}</p>
          </div>
        </Panel>
      </div>

      <Panel title="Limitations" className="mt-4">
        <div className="space-y-2">
          {m.limitations.map((l, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <Badge status="warning">Note</Badge>
              <span className="text-paper-dim">{l}</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
