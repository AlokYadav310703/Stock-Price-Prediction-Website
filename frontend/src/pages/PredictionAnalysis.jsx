import React, { useState } from 'react'
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import {
  PageHeader,
  Panel,
  MetricCard,
  LoadingState,
  ErrorState,
  EmptyState,
  DirectionTag,
  ResultTag,
  fmtUSD,
} from '../components/ui'

const RANGES = [
  ['7d', '7D'],
  ['30d', '30D'],
  ['90d', '90D'],
  ['1y', '1Y'],
  ['all', 'All'],
]

export default function PredictionAnalysis() {
  const [range, setRange] = useState('90d')

  const { data, loading, error, reload } = useAsync(
    () => Promise.all([api.getPredictionsInRange(range), api.getPerformanceMetrics(range)]),
    [range],
  )

  return (
    <div>
      <PageHeader
        eyebrow="Prediction Analysis"
        title="Actual vs Predicted Prices"
        description="Historical prediction performance, direction correctness, and error metrics computed from stored prediction logs."
        right={
          <div className="flex gap-1 bg-ink-800 border border-ink-600 rounded-lg p-1">
            {RANGES.map(([key, label]) => (
              <button
                key={key}
                onClick={() => setRange(key)}
                className={`text-xs font-medium px-3 py-1.5 rounded-md transition-colors ${
                  range === key ? 'bg-accent-dim text-paper border border-accent/40' : 'text-paper-dim hover:text-paper'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        }
      />

      {loading && <LoadingState label="Crunching prediction history…" />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && (
        <AnalysisBody rows={data[0]} perf={data[1]} />
      )}
    </div>
  )
}

function AnalysisBody({ rows, perf }) {
  if (!rows || rows.length === 0) {
    return <EmptyState title="No predictions in this range" message="Insufficient data." />
  }

  const chartData = rows.map((r) => ({
    date: r.prediction_date,
    Actual: r.actual_price,
    Predicted: r.predicted_price,
    diff: r.error,
    pct: r.percentage_error,
    correct: r.is_correct,
  }))

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Directional Accuracy" value={perf.insufficient_data ? '—' : `${perf.directional_accuracy}%`} />
        <MetricCard label="Correct Predictions" value={perf.insufficient_data ? '—' : perf.correct} />
        <MetricCard label="Incorrect Predictions" value={perf.insufficient_data ? '—' : perf.incorrect} />
        <MetricCard label="Total Predictions" value={perf.insufficient_data ? '—' : perf.total} />
      </div>

      <Panel title="Actual vs Predicted Price" subtitle="Hover a point for date, prices, error and result">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#232B3D" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#8993A8' }} stroke="#232B3D" minTickGap={24} />
              <YAxis tick={{ fontSize: 11, fill: '#8993A8' }} stroke="#232B3D" domain={['auto', 'auto']} />
              <Tooltip content={<AnalysisTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="Actual" stroke="#2FBF8F" dot={false} strokeWidth={2} connectNulls />
              <Line type="monotone" dataKey="Predicted" stroke="#4C7EFF" dot={false} strokeWidth={1.5} strokeDasharray="4 3" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <Panel title="Regression Metrics">
          {perf.insufficient_data ? (
            <p className="text-sm text-paper-dim">Insufficient data</p>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <Stat label="MAE" value={perf.mae} />
              <Stat label="RMSE" value={perf.rmse} />
              <Stat label="MAPE" value={`${perf.mape}%`} />
              <Stat label="R²" value={perf.r2 ?? '—'} />
            </div>
          )}
        </Panel>
        <Panel title="Directional Metrics">
          {perf.insufficient_data ? (
            <p className="text-sm text-paper-dim">Insufficient data</p>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <Stat label="Accuracy" value={`${perf.directional_accuracy}%`} />
              <Stat label="Total" value={perf.total} />
              <Stat label="Correct" value={perf.correct} tone="up" />
              <Stat label="Incorrect" value={perf.incorrect} tone="down" />
            </div>
          )}
        </Panel>
      </div>

      <Panel title="Correct vs Incorrect Predictions" className="mt-4">
        <div className="overflow-x-auto -mx-5 px-5">
          <table className="w-full text-sm min-w-[720px]">
            <thead>
              <tr className="text-left text-xs text-paper-dim uppercase tracking-wide border-b border-ink-600">
                <th className="py-2 pr-4 font-medium">Date</th>
                <th className="py-2 pr-4 font-medium">Predicted</th>
                <th className="py-2 pr-4 font-medium">Actual</th>
                <th className="py-2 pr-4 font-medium">Error</th>
                <th className="py-2 pr-4 font-medium">Direction</th>
                <th className="py-2 pr-4 font-medium">Result</th>
              </tr>
            </thead>
            <tbody>
              {rows
                .filter((r) => r.actual_price != null)
                .slice()
                .reverse()
                .map((r) => (
                  <tr key={r.id} className="border-b border-ink-600/60 last:border-0">
                    <td className="py-2.5 pr-4 num text-paper-dim">{r.prediction_date}</td>
                    <td className="py-2.5 pr-4 num text-paper">{fmtUSD(r.predicted_price)}</td>
                    <td className="py-2.5 pr-4 num text-paper">{fmtUSD(r.actual_price)}</td>
                    <td className="py-2.5 pr-4 num text-paper-dim">{fmtUSD(Math.abs(r.error))}</td>
                    <td className="py-2.5 pr-4">
                      <DirectionTag direction={r.predicted_direction} />
                    </td>
                    <td className="py-2.5 pr-4">
                      <ResultTag isCorrect={r.is_correct} />
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  )
}

function AnalysisTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null
  const row = payload[0]?.payload
  return (
    <div className="bg-ink-800 border border-ink-600 rounded-lg p-3 text-xs shadow-panel">
      <div className="num text-paper font-semibold mb-1">{label}</div>
      <div className="text-paper-dim">Actual: <span className="num text-paper">{row.Actual != null ? fmtUSD(row.Actual) : '—'}</span></div>
      <div className="text-paper-dim">Predicted: <span className="num text-paper">{fmtUSD(row.Predicted)}</span></div>
      {row.diff != null && (
        <>
          <div className="text-paper-dim">Difference: <span className="num text-paper">{row.diff.toFixed(2)}</span></div>
          <div className="text-paper-dim">% Error: <span className="num text-paper">{row.pct.toFixed(2)}%</span></div>
          <div className="mt-1">
            {row.correct ? (
              <span className="text-signal-up">✓ Correct</span>
            ) : (
              <span className="text-signal-down">✗ Incorrect</span>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function Stat({ label, value, tone }) {
  const color = tone === 'up' ? 'text-signal-up' : tone === 'down' ? 'text-signal-down' : 'text-paper'
  return (
    <div>
      <div className="text-xs text-paper-dim mb-1">{label}</div>
      <div className={`num text-lg font-semibold ${color}`}>{value}</div>
    </div>
  )
}
