import React from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { PageHeader, Panel, MetricCard, LoadingState, ErrorState, Badge } from '../components/ui'

const DRIFT_STATUS = {
  normal: 'normal',
  warning: 'warning',
  high_drift: 'high_drift',
}
const DRIFT_LABEL = { normal: 'Normal', warning: 'Warning', high_drift: 'High Drift' }

export default function ModelMonitoring() {
  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([
        api.getPerformanceTrend(),
        api.getPredictionDistribution(),
        api.getDataQuality(),
        api.getDriftReport(),
        api.getModelHealth(),
      ]),
    [],
  )

  if (loading) return <LoadingState label="Running monitoring checks…" />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const [trend, distribution, quality, drift, health] = data

  return (
    <div>
      <PageHeader
        eyebrow="Model Monitoring"
        title="Model, Data &amp; Drift Monitoring"
        description="Automated checks run once per trading day alongside the prediction job. All figures below come from stored logs — nothing here is hardcoded."
      />

      {/* A. Model performance over time */}
      <Panel title="Model Performance Over Time" subtitle="Weekly rolling MAE, RMSE and directional accuracy">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trend} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#232B3D" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#8993A8' }} stroke="#232B3D" minTickGap={20} />
              <YAxis tick={{ fontSize: 11, fill: '#8993A8' }} stroke="#232B3D" />
              <Tooltip contentStyle={{ background: '#161D2B', border: '1px solid #232B3D', borderRadius: 8, fontSize: 12 }} />
              <Line type="monotone" dataKey="mae" name="MAE" stroke="#4C7EFF" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="directional_accuracy" name="Dir. Accuracy %" stroke="#2FBF8F" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        {/* B. Prediction distribution */}
        <Panel title="Prediction Distribution" subtitle="Predicted direction over the last 60 trading days">
          <div className="h-56 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[
                  { name: 'UP', count: distribution.direction_counts.UP },
                  { name: 'DOWN', count: distribution.direction_counts.DOWN },
                  { name: 'FLAT', count: distribution.direction_counts.FLAT },
                ]}
                margin={{ top: 5, right: 10, left: -10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#232B3D" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#8993A8' }} stroke="#232B3D" />
                <YAxis tick={{ fontSize: 11, fill: '#8993A8' }} stroke="#232B3D" allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#161D2B', border: '1px solid #232B3D', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  <Cell fill="#2FBF8F" />
                  <Cell fill="#E5484D" />
                  <Cell fill="#8993A8" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-paper-dim">
            Sustained skew toward one direction, or a sudden shift from the historical mix, can indicate the model is
            over-reacting to a regime change rather than genuine signal.
          </p>
        </Panel>

        {/* C. Data quality */}
        <Panel title="Data Quality" subtitle={`${quality.total_records.toLocaleString()} records monitored`}>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <QualityStat label="Missing Values" value={quality.missing_values} />
            <QualityStat label="Duplicates" value={quality.duplicate_records} />
            <QualityStat label="Invalid Values" value={quality.invalid_values} />
          </div>
          <div className="space-y-2">
            {quality.checks.map((c, i) => (
              <div key={i} className="flex items-start justify-between gap-3 text-xs py-1.5 border-b border-ink-600/60 last:border-0">
                <div>
                  <div className="text-paper font-medium">{c.name}</div>
                  <div className="text-paper-dim mt-0.5">{c.detail}</div>
                </div>
                <Badge status={c.status === 'ok' ? 'ok' : 'warning'}>{c.status === 'ok' ? 'OK' : 'Warning'}</Badge>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* D. Data drift */}
      <Panel
        title="Data Drift"
        subtitle={`${drift.reference_window} vs. ${drift.comparison_window} · thresholds: warning ≥ ${drift.thresholds.warning}, high drift ≥ ${drift.thresholds.high_drift}`}
        className="mt-4"
      >
        <div className="overflow-x-auto -mx-5 px-5">
          <table className="w-full text-sm min-w-[520px]">
            <thead>
              <tr className="text-left text-xs text-paper-dim uppercase tracking-wide border-b border-ink-600">
                <th className="py-2 pr-4 font-medium">Feature</th>
                <th className="py-2 pr-4 font-medium">PSI</th>
                <th className="py-2 pr-4 font-medium">KS Statistic</th>
                <th className="py-2 pr-4 font-medium">Drift Status</th>
              </tr>
            </thead>
            <tbody>
              {drift.features.map((f) => (
                <tr key={f.feature} className="border-b border-ink-600/60 last:border-0">
                  <td className="py-2.5 pr-4 text-paper">{f.feature}</td>
                  <td className="py-2.5 pr-4 num text-paper-dim">{f.psi.toFixed(2)}</td>
                  <td className="py-2.5 pr-4 num text-paper-dim">{f.ks.toFixed(2)}</td>
                  <td className="py-2.5 pr-4">
                    <Badge status={DRIFT_STATUS[f.status]}>{DRIFT_LABEL[f.status]}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Model health */}
      <Panel title="Model Health" className="mt-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <MetricCard label="Model Status" value={<Badge status="healthy">{health.status}</Badge>} />
          <MetricCard label="Last Prediction" value={health.last_prediction} />
          <MetricCard label="Model Version" value={health.model_version} />
          <MetricCard label="Prediction Count" value={health.prediction_count} />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {Object.entries(health.checks).map(([key, ok]) => (
            <div key={key} className="panel p-3 flex items-center justify-between">
              <span className="text-xs text-paper-dim capitalize">{key.replaceAll('_', ' ')}</span>
              <Badge status={ok ? 'ok' : 'critical'}>{ok ? 'OK' : 'Fail'}</Badge>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}

function QualityStat({ label, value }) {
  return (
    <div className="panel p-3 text-center">
      <div className="num text-lg font-semibold text-paper">{value}</div>
      <div className="text-[11px] text-paper-dim mt-0.5">{label}</div>
    </div>
  )
}
