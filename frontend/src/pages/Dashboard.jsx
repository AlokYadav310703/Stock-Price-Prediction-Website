import React from 'react'
import {
  ResponsiveContainer,
  LineChart,
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
  DirectionTag,
  ResultTag,
  fmtUSD,
  fmtPct,
} from '../components/ui'

export default function Dashboard() {
  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([
        api.getStockSummary(),
        api.getLatestPrediction(),
        api.getPerformanceMetrics('90d'),
        api.getPredictions({ limit: 10 }),
        api.getPredictionsInRange('30d'),
      ]),
    [],
  )

  if (loading) return <LoadingState label="Loading dashboard…" />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const [stock, prediction, perf, recent, trend] = data
  const chartData = trend.map((r) => ({
    date: r.prediction_date.slice(5),
    Actual: r.actual_price,
    Predicted: r.predicted_price,
  }))

  const priceUp = stock.change >= 0
  const predDelta = prediction.predicted_price - stock.current_price

  return (
    <div>
      <PageHeader
        eyebrow={`${stock.symbol} · ${stock.name}`}
        title="Dashboard"
        description={`Overview of the current prediction and model status. Prices as of ${stock.as_of}.`}
      />

      {/* Hero row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="Current Price"
          value={fmtUSD(stock.current_price)}
          delta={fmtPct(stock.change_pct)}
          deltaGood={priceUp}
          hint={`${priceUp ? '+' : ''}${stock.change} today`}
        />
        <MetricCard
          label="Predicted Next-Day Price"
          value={fmtUSD(prediction.predicted_price)}
          delta={`${predDelta >= 0 ? '+' : ''}${predDelta.toFixed(2)}`}
          deltaGood={predDelta >= 0}
          hint={`Target date ${prediction.target_date}`}
        />
        <MetricCard
          label="Prediction Direction"
          value={<DirectionTag direction={prediction.predicted_direction} />}
          hint={`Previous prediction ${fmtUSD(prediction.previous_prediction)}`}
        />
        <MetricCard
          label="Directional Accuracy (90d)"
          value={perf.insufficient_data ? '—' : `${perf.directional_accuracy}%`}
          hint={perf.insufficient_data ? 'Insufficient data' : `${perf.correct}/${perf.total} correct`}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Trend chart */}
        <Panel title="Actual vs Predicted — Last 30 Days" subtitle="Trading-day close price" className="xl:col-span-2">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#232B3D" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#8993A8' }} stroke="#232B3D" />
                <YAxis tick={{ fontSize: 11, fill: '#8993A8' }} stroke="#232B3D" domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ background: '#161D2B', border: '1px solid #232B3D', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#E8ECF2' }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="Actual" stroke="#2FBF8F" dot={false} strokeWidth={2} connectNulls />
                <Line type="monotone" dataKey="Predicted" stroke="#4C7EFF" dot={false} strokeWidth={2} strokeDasharray="4 3" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        {/* Model performance summary */}
        <Panel title="Model Performance" subtitle="Trailing 90 trading days">
          {perf.insufficient_data ? (
            <p className="text-sm text-paper-dim">Insufficient data</p>
          ) : (
            <div className="space-y-3">
              <StatRow label="MAE" value={perf.mae} />
              <StatRow label="RMSE" value={perf.rmse} />
              <StatRow label="MAPE" value={`${perf.mape}%`} />
              <StatRow label="R²" value={perf.r2 ?? '—'} />
              <StatRow label="Correct" value={perf.correct} accent="up" />
              <StatRow label="Incorrect" value={perf.incorrect} accent="down" />
              <StatRow label="Total Predictions" value={perf.total} />
            </div>
          )}
        </Panel>
      </div>

      <Panel title="Recent Predictions" subtitle="Most recent 10 trading days" className="mt-4">
        <div className="overflow-x-auto -mx-5 px-5">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-left text-xs text-paper-dim uppercase tracking-wide border-b border-ink-600">
                <th className="py-2 pr-4 font-medium">Date</th>
                <th className="py-2 pr-4 font-medium">Predicted</th>
                <th className="py-2 pr-4 font-medium">Actual</th>
                <th className="py-2 pr-4 font-medium">Direction</th>
                <th className="py-2 pr-4 font-medium">Result</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.id} className="border-b border-ink-600/60 last:border-0">
                  <td className="py-2.5 pr-4 num text-paper-dim">{r.prediction_date}</td>
                  <td className="py-2.5 pr-4 num text-paper">{fmtUSD(r.predicted_price)}</td>
                  <td className="py-2.5 pr-4 num text-paper">{r.actual_price != null ? fmtUSD(r.actual_price) : '—'}</td>
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
    </div>
  )
}

function StatRow({ label, value, accent }) {
  const color = accent === 'up' ? 'text-signal-up' : accent === 'down' ? 'text-signal-down' : 'text-paper'
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-paper-dim">{label}</span>
      <span className={`num text-sm font-semibold ${color}`}>{value}</span>
    </div>
  )
}
