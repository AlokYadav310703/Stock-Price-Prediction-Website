import axios from 'axios'
import * as mock from './mockData'

// ─────────────────────────────────────────────────────────────────────────
// Toggle: when the FastAPI backend exists, set VITE_USE_MOCK_DATA=false
// and VITE_API_BASE_URL in .env. Every page imports functions from this
// file only — none of them know or care whether data is mocked.
// ─────────────────────────────────────────────────────────────────────────

const USE_MOCK = (import.meta.env.VITE_USE_MOCK_DATA ?? 'true') !== 'false'
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const http = axios.create({ baseURL: BASE_URL, timeout: 180000 })

// Simulated network latency so loading states are visible/testable in the mock build.
const delay = (ms = 350) => new Promise((res) => setTimeout(res, ms))

async function call(mockFn, realPath, params) {
  if (USE_MOCK) {
    await delay()
    return mockFn()
  }
  const { data } = await http.get(realPath, { params })
  return data
}

export const api = {
  health: () => call(() => ({ status: 'ok' }), '/health'),
  getStockSummary: () => call(mock.getStockSummary, '/stock/summary'),
  getLatestPrediction: () => call(mock.getLatestPrediction, '/prediction/latest'),
  getPredictionDetail: () => call(mock.getPredictionDetail, '/prediction/latest/detail'),
  getPredictions: (params) => call(() => mock.getPredictions(params), '/predictions', params),
  getPredictionByDate: (date) => call(() => mock.getPredictionByDate(date), `/predictions/${date}`),
  getPredictionsInRange: (range) => call(() => mock.getPredictionsInRange(range), '/predictions', { range }),
  getPerformanceMetrics: (range) => call(() => mock.getPerformanceMetrics(range), '/performance', { range }),
  getPerformanceTrend: () => call(mock.getPerformanceTrend, '/performance/trend'),
  getDataQuality: () => call(mock.getDataQuality, '/data-quality'),
  getDriftReport: () => call(mock.getDriftReport, '/drift'),
  getPredictionDistribution: () => call(mock.getPredictionDistribution, '/monitoring/distribution'),
  getAlerts: () => call(mock.getAlerts, '/alerts'),
  getModelHealth: () => call(mock.getModelHealth, '/monitoring/health'),
  getAboutModel: () => call(mock.getAboutModel, '/model/about'),
}

export default api
