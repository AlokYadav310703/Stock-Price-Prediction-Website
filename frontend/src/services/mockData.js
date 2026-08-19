// ─────────────────────────────────────────────────────────────────────────
// Mock data layer.
//
// Every function here returns data shaped exactly like the future FastAPI
// responses described in the backend spec (Prediction, alerts, monitoring,
// model health). When the backend is ready, only src/services/api.js needs
// to change — no page or component in this app touches this file directly.
// ─────────────────────────────────────────────────────────────────────────

const SYMBOL = 'AAPL'
const COMPANY = 'Apple Inc.'
const MODEL_VERSION = 'v2.3.1'

// Deterministic pseudo-random so the mock data is stable across renders.
function mulberry32(seed) {
  return function () {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const rand = mulberry32(20260817)

function isTradingDay(date) {
  const day = date.getDay()
  return day !== 0 && day !== 6
}

function addDays(date, n) {
  const d = new Date(date)
  d.setDate(d.getDate() + n)
  return d
}

function fmtDate(date) {
  return date.toISOString().slice(0, 10)
}

// ── Generate ~150 calendar days of trading-day prediction history ─────────
function generateHistory() {
  const today = new Date('2026-08-17T00:00:00Z')
  const days = []
  let cursor = addDays(today, -210)
  while (cursor <= today) {
    if (isTradingDay(cursor)) days.push(new Date(cursor))
    cursor = addDays(cursor, 1)
  }

  let price = 227.5
  const rows = []
  let id = 1

  for (let i = 0; i < days.length; i++) {
    const predictionDate = days[i]
    const targetDate = days[i + 1] || addDays(predictionDate, 1)

    // Simulate a mildly-trending, noisy walk for the "actual" price.
    const drift = Math.sin(i / 18) * 0.35
    const noise = (rand() - 0.5) * 4.2
    const nextActual = i < days.length - 1 ? Math.max(140, price + drift + noise) : null

    // Model prediction: mostly tracks direction with realistic error.
    const modelNoise = (rand() - 0.5) * 3.4
    const modelBias = (rand() - 0.48) * 1.6
    const predictedPrice = price + drift + modelBias + modelNoise

    const predictedDirection = predictedPrice > price ? 'UP' : predictedPrice < price ? 'DOWN' : 'FLAT'
    let actualPrice = null
    let actualDirection = null
    let isCorrect = null
    let error = null
    let absError = null
    let pctError = null

    // The 3 most recent trading days have no actual price yet (pending).
    const isPending = i >= days.length - 3
    if (!isPending && nextActual != null) {
      actualPrice = nextActual
      actualDirection = actualPrice > price ? 'UP' : actualPrice < price ? 'DOWN' : 'FLAT'
      isCorrect = predictedDirection === actualDirection
      error = predictedPrice - actualPrice
      absError = Math.abs(error)
      pctError = (absError / actualPrice) * 100
    }

    rows.push({
      id: id++,
      prediction_date: fmtDate(predictionDate),
      target_date: fmtDate(targetDate),
      base_price: Number(price.toFixed(2)),
      predicted_price: Number(predictedPrice.toFixed(2)),
      actual_price: actualPrice != null ? Number(actualPrice.toFixed(2)) : null,
      predicted_direction: predictedDirection,
      actual_direction: actualDirection,
      is_correct: isCorrect,
      error: error != null ? Number(error.toFixed(2)) : null,
      absolute_error: absError != null ? Number(absError.toFixed(2)) : null,
      percentage_error: pctError != null ? Number(pctError.toFixed(2)) : null,
      model_version: MODEL_VERSION,
      created_at: `${fmtDate(predictionDate)}T16:05:00Z`,
    })

    if (nextActual != null) price = nextActual
  }

  return rows
}

const HISTORY = generateHistory()

export function getStockSummary() {
  const last = HISTORY[HISTORY.length - 1]
  const prevClose = HISTORY[HISTORY.length - 2].base_price
  return {
    symbol: SYMBOL,
    name: COMPANY,
    current_price: last.base_price,
    previous_close: prevClose,
    change: Number((last.base_price - prevClose).toFixed(2)),
    change_pct: Number((((last.base_price - prevClose) / prevClose) * 100).toFixed(2)),
    as_of: last.prediction_date,
  }
}

export function getLatestPrediction() {
  const last = HISTORY[HISTORY.length - 1]
  const prior = HISTORY[HISTORY.length - 2]
  return {
    ...last,
    previous_prediction: prior.predicted_price,
    model_version: MODEL_VERSION,
  }
}

export function getPredictionDetail() {
  const last = HISTORY[HISTORY.length - 1]
  const currentPrice = last.base_price
  const stage1Pred = Number((last.predicted_price + (rand() - 0.5) * 1.2).toFixed(2))
  const lstm = Number((stage1Pred + (rand() - 0.5) * 0.8).toFixed(2))
  const cnn = Number((stage1Pred + (rand() - 0.5) * 0.8).toFixed(2))
  const correction = Number((last.predicted_price - stage1Pred).toFixed(2))
  const sentiment = Number((rand() * 2 - 1).toFixed(2))
  const impact = Number(rand().toFixed(2))
  const eventWeight = Number(rand().toFixed(2))
  const return1d = Number(((last.base_price / HISTORY[HISTORY.length - 2].base_price - 1) * 100).toFixed(2))
  const return5d = Number(((last.base_price / HISTORY[HISTORY.length - 6].base_price - 1) * 100).toFixed(2))
  const expectedMovePct = ((last.predicted_price - currentPrice) / currentPrice) * 100

  let recommendation = 'HOLD'
  if (expectedMovePct > 2) recommendation = 'STRONG BUY'
  else if (expectedMovePct > 0.5) recommendation = 'BUY'
  else if (expectedMovePct < -2) recommendation = 'STRONG SELL'
  else if (expectedMovePct < -0.5) recommendation = 'SELL'

  return {
    prediction_date: last.prediction_date,
    target_date: last.target_date,
    model_version: MODEL_VERSION,
    current_price: currentPrice,
    stage1_prediction: stage1Pred,
    base_predictions: { lstm, cnn },
    final_prediction: last.predicted_price,
    correction,
    news_features: {
      sentiment_score: sentiment,
      impact_score: impact,
      event_weight: eventWeight,
      news_count: 3,
      has_supply_chain_event: rand() > 0.85 ? 1 : 0,
    },
    market_returns: { return_1d: return1d, return_5d: return5d },
    expected_move_pct: Number(expectedMovePct.toFixed(2)),
    recommendation,
    similar_events: [
      { title: 'Apple supplier reports stronger-than-expected component orders', date: '2026-08-12', similarity: 0.87, direction: 'POSITIVE' },
      { title: 'Analyst note flags softer iPhone demand in one region', date: '2026-08-09', similarity: 0.74, direction: 'NEGATIVE' },
      { title: 'Routine product-cycle coverage ahead of the next launch window', date: '2026-08-04', similarity: 0.61, direction: 'NEUTRAL' },
    ],
  }
}

export function getPredictions({ limit = 30 } = {}) {
  return HISTORY.slice(-limit).reverse()
}

export function getPredictionByDate(date) {
  return HISTORY.find((r) => r.prediction_date === date) || null
}

export function getPredictionsInRange(range) {
  // range: '7d' | '30d' | '90d' | '1y' | 'all'
  const map = { '7d': 7, '30d': 30, '90d': 90, '1y': 365 }
  if (range === 'all') return HISTORY
  const n = map[range] ?? 30
  return HISTORY.slice(-n)
}

export function getPerformanceMetrics(range = '90d') {
  const rows = getPredictionsInRange(range).filter((r) => r.actual_price != null)
  if (rows.length === 0) {
    return { insufficient_data: true }
  }
  const n = rows.length
  const mae = rows.reduce((s, r) => s + r.absolute_error, 0) / n
  const rmse = Math.sqrt(rows.reduce((s, r) => s + r.error * r.error, 0) / n)
  const mape = rows.reduce((s, r) => s + r.percentage_error, 0) / n
  const correct = rows.filter((r) => r.is_correct).length
  const incorrect = n - correct

  // R^2 vs. naive "no change" baseline
  const meanActual = rows.reduce((s, r) => s + r.actual_price, 0) / n
  const ssRes = rows.reduce((s, r) => s + (r.actual_price - r.predicted_price) ** 2, 0)
  const ssTot = rows.reduce((s, r) => s + (r.actual_price - meanActual) ** 2, 0)
  const r2 = ssTot === 0 ? null : 1 - ssRes / ssTot

  return {
    insufficient_data: false,
    mae: Number(mae.toFixed(3)),
    rmse: Number(rmse.toFixed(3)),
    mape: Number(mape.toFixed(3)),
    r2: r2 != null ? Number(r2.toFixed(3)) : null,
    directional_accuracy: Number(((correct / n) * 100).toFixed(1)),
    correct,
    incorrect,
    total: n,
  }
}

export function getPerformanceTrend() {
  // Weekly rolling directional accuracy / MAE over the last ~26 weeks.
  const withActual = HISTORY.filter((r) => r.actual_price != null)
  const weeks = []
  for (let i = 0; i < withActual.length; i += 5) {
    const chunk = withActual.slice(i, i + 5)
    if (chunk.length === 0) continue
    const mae = chunk.reduce((s, r) => s + r.absolute_error, 0) / chunk.length
    const rmse = Math.sqrt(chunk.reduce((s, r) => s + r.error ** 2, 0) / chunk.length)
    const acc = (chunk.filter((r) => r.is_correct).length / chunk.length) * 100
    weeks.push({
      date: chunk[chunk.length - 1].prediction_date,
      mae: Number(mae.toFixed(2)),
      rmse: Number(rmse.toFixed(2)),
      directional_accuracy: Number(acc.toFixed(1)),
    })
  }
  return weeks
}

export function getDataQuality() {
  return {
    records_last_24h: 1,
    total_records: HISTORY.length,
    missing_values: 0,
    duplicate_records: 0,
    invalid_values: 0,
    checks: [
      { name: 'OHLC completeness', status: 'ok', detail: 'No missing Open/High/Low/Close fields in the last fetch.' },
      { name: 'Row freshness', status: 'ok', detail: 'Latest row is dated within the current trading session.' },
      { name: 'Duplicate rows', status: 'ok', detail: 'No duplicate (symbol, date) pairs found.' },
      { name: 'Value range check', status: 'warning', detail: 'Intraday volume 18% above trailing 30-day average.' },
    ],
  }
}

export function getDriftReport() {
  return {
    reference_window: 'Training set (2024-01-01 – 2025-12-31)',
    comparison_window: 'Last 30 trading days',
    features: [
      { feature: 'RSI', psi: 0.04, ks: 0.06, status: 'normal' },
      { feature: 'MACD', psi: 0.07, ks: 0.09, status: 'normal' },
      { feature: 'Volume', psi: 0.19, ks: 0.21, status: 'warning' },
      { feature: 'ATR', psi: 0.05, ks: 0.07, status: 'normal' },
      { feature: 'Momentum', psi: 0.31, ks: 0.28, status: 'high_drift' },
      { feature: 'Sentiment Score', psi: 0.08, ks: 0.1, status: 'normal' },
    ],
    thresholds: { warning: 0.15, high_drift: 0.25 },
  }
}

export function getPredictionDistribution() {
  const recent = HISTORY.slice(-60)
  return {
    predicted_changes: recent.map((r) => Number((r.predicted_price - r.base_price).toFixed(2))),
    direction_counts: {
      UP: recent.filter((r) => r.predicted_direction === 'UP').length,
      DOWN: recent.filter((r) => r.predicted_direction === 'DOWN').length,
      FLAT: recent.filter((r) => r.predicted_direction === 'FLAT').length,
    },
  }
}

export function getAlerts() {
  return [
    {
      id: 5,
      alert_type: 'DRIFT',
      severity: 'WARNING',
      message: "Feature 'Momentum' shows high drift (PSI 0.31, threshold 0.25) versus the training reference window.",
      created_at: '2026-08-17T06:10:00Z',
      resolved: false,
    },
    {
      id: 4,
      alert_type: 'PERFORMANCE',
      severity: 'WARNING',
      message: 'Directional accuracy over the trailing 10 predictions dropped to 52.0%, below the 55% threshold.',
      created_at: '2026-08-15T06:12:00Z',
      resolved: false,
    },
    {
      id: 3,
      alert_type: 'DATA_QUALITY',
      severity: 'INFO',
      message: 'Intraday volume for AAPL is 18% above its trailing 30-day average.',
      created_at: '2026-08-14T06:05:00Z',
      resolved: true,
    },
    {
      id: 2,
      alert_type: 'JOB',
      severity: 'CRITICAL',
      message: "Scheduled job 'update_actual_prices' failed after 3 retries: market data API timeout.",
      created_at: '2026-08-05T06:20:00Z',
      resolved: true,
    },
    {
      id: 1,
      alert_type: 'PERFORMANCE',
      severity: 'INFO',
      message: 'Weekly performance report generated: MAE 2.14, directional accuracy 64.0%.',
      created_at: '2026-08-01T06:15:00Z',
      resolved: true,
    },
  ]
}

export function getModelHealth() {
  const perf = getPerformanceMetrics('90d')
  const last = HISTORY[HISTORY.length - 1]
  return {
    status: 'healthy',
    last_prediction: last.prediction_date,
    last_training: '2026-06-02',
    model_version: MODEL_VERSION,
    prediction_count: HISTORY.length,
    directional_accuracy: perf.insufficient_data ? null : perf.directional_accuracy,
    checks: {
      model_file_exists: true,
      prediction_pipeline_working: true,
      last_scheduled_job_succeeded: true,
      database_connected: true,
      market_data_api_working: true,
    },
  }
}

export function getAboutModel() {
  return {
    name: 'AAPL Next-Day Price Predictor',
    version: MODEL_VERSION,
    architecture: [
      { stage: 'Stage 1 — Ensemble', detail: 'LSTM and CNN base learners trained on 30-day OHLC windows, combined by a meta-learner into a single next-day price estimate.' },
      { stage: 'Stage 2 — News-aware correction', detail: 'A gradient-boosted regressor adjusts the Stage 1 estimate using same-day news sentiment, impact and event-weight features retrieved via similarity search, plus 1-day and 5-day market returns.' },
    ],
    features: [
      'Open / High / Low / Close (30-day window)',
      '1-day and 5-day price returns',
      'News sentiment score (vector-similarity weighted)',
      'News impact score',
      'Event weight (e.g. supply-chain events)',
    ],
    training_period: 'Jan 2024 – Dec 2025',
    prediction_methodology:
      'A scheduled job runs once per trading day after market close, fetches the latest OHLC data, computes technical indicators and news features, runs the two-stage model, and stores the prediction. Actual prices are matched automatically the following trading day.',
    limitations: [
      'Directional accuracy, not price-level accuracy, is the primary success metric — exact price matches are not expected.',
      'News coverage gaps (no matching similarity events) fall back to neutral sentiment features, which can understate reaction to fast-breaking news.',
      'The model has not been retrained on data after Dec 2025 and may drift during regime changes.',
      'Not intended as financial advice; outputs are informational only.',
    ],
  }
}
