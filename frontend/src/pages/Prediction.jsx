import React from 'react'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { PageHeader, Panel, MetricCard, LoadingState, ErrorState, Badge, fmtUSD, fmtPct } from '../components/ui'

const REC_STYLES = {
  'STRONG BUY': 'up',
  BUY: 'up',
  HOLD: 'neutral',
  SELL: 'down',
  'STRONG SELL': 'down',
}

export default function Prediction() {
  const { data, loading, error, reload } = useAsync(() => api.getPredictionDetail(), [])

  if (loading) return <LoadingState label="Loading current prediction…" />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const p = data
  const recTone = REC_STYLES[p.recommendation] || 'neutral'

  return (
    <div>
      <PageHeader
        eyebrow={`Prediction dated ${p.prediction_date}`}
        title="Current Prediction"
        description={`Full two-stage pipeline output for target date ${p.target_date} · Model ${p.model_version}`}
      />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <MetricCard label="Current Price" value={fmtUSD(p.current_price)} />
        <MetricCard
          label="Stage 1 Prediction"
          value={fmtUSD(p.stage1_prediction)}
          delta={(p.stage1_prediction - p.current_price).toFixed(2)}
          hint="Ensemble (LSTM + CNN)"
        />
        <MetricCard
          label="Final Prediction"
          value={fmtUSD(p.final_prediction)}
          delta={(p.final_prediction - p.current_price).toFixed(2)}
          hint="After news-aware correction"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Panel title="Stage 1 · Base Learners" subtitle="30-day OHLC window ensemble">
          <div className="grid grid-cols-2 gap-4">
            <SubMetric label="LSTM Model" value={fmtUSD(p.base_predictions.lstm)} delta={p.base_predictions.lstm - p.current_price} />
            <SubMetric label="CNN Model" value={fmtUSD(p.base_predictions.cnn)} delta={p.base_predictions.cnn - p.current_price} />
          </div>
        </Panel>

        <Panel title="Stage 2 · News-Aware Correction" subtitle="Gradient-boosted adjustment">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-paper-dim mb-1">Adjustment</div>
              <div className={`num text-xl font-semibold ${p.correction >= 0 ? 'text-signal-up' : 'text-signal-down'}`}>
                {p.correction >= 0 ? '+' : ''}
                {fmtUSD(p.correction)}
              </div>
            </div>
            <Badge status={p.correction >= 0 ? 'correct' : 'incorrect'}>
              {p.correction >= 0 ? 'Bullish' : 'Bearish'} adjustment
            </Badge>
          </div>
        </Panel>

        <Panel title="News Sentiment Inputs" subtitle={`${p.news_features.news_count} articles analyzed`}>
          <div className="grid grid-cols-3 gap-4">
            <SubMetric label="Sentiment" value={p.news_features.sentiment_score} />
            <SubMetric label="Impact Score" value={p.news_features.impact_score} />
            <SubMetric label="Event Weight" value={p.news_features.event_weight} />
          </div>
          {p.news_features.has_supply_chain_event ? (
            <div className="mt-4 text-xs text-signal-warn">⚠ Supply chain event detected in recent coverage</div>
          ) : (
            <div className="mt-4 text-xs text-signal-up">✓ No supply chain issues flagged</div>
          )}
        </Panel>

        <Panel title="Market Technical Indicators">
          <div className="grid grid-cols-2 gap-4">
            <SubMetric label="1-Day Return" value={fmtPct(p.market_returns.return_1d)} />
            <SubMetric label="5-Day Return" value={fmtPct(p.market_returns.return_5d)} />
          </div>
        </Panel>
      </div>

      <Panel title="Similar Historical Events" subtitle="Top matches from vector similarity search" className="mt-4">
        <div className="space-y-3">
          {p.similar_events.map((ev, i) => (
            <div key={i} className="flex items-center justify-between gap-4 py-2 border-b border-ink-600/60 last:border-0">
              <div className="min-w-0">
                <div className="text-sm text-paper truncate">{ev.title}</div>
                <div className="text-xs text-paper-dim num mt-0.5">{ev.date}</div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="num text-xs text-paper-dim">{(ev.similarity * 100).toFixed(0)}% match</span>
                <Badge status={ev.direction === 'POSITIVE' ? 'correct' : ev.direction === 'NEGATIVE' ? 'incorrect' : 'neutral'}>
                  {ev.direction}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="Trading Signal"
        subtitle={`Expected move ${fmtPct(p.expected_move_pct)} to ${fmtUSD(p.final_prediction)}`}
        className="mt-4"
      >
        <div className="flex items-center gap-3">
          <Badge status={recTone === 'up' ? 'correct' : recTone === 'down' ? 'incorrect' : 'neutral'}>
            {p.recommendation}
          </Badge>
          <span className="text-sm text-paper-dim">
            Derived from the model's expected move — informational only, not financial advice.
          </span>
        </div>
      </Panel>
    </div>
  )
}

function SubMetric({ label, value, delta }) {
  return (
    <div>
      <div className="text-xs text-paper-dim mb-1">{label}</div>
      <div className="num text-base font-semibold text-paper">{value}</div>
      {delta != null && (
        <div className={`num text-xs mt-0.5 ${delta >= 0 ? 'text-signal-up' : 'text-signal-down'}`}>
          {delta >= 0 ? '+' : ''}
          {delta.toFixed(2)}
        </div>
      )}
    </div>
  )
}
