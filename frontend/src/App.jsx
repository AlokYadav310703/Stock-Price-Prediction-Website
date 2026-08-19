import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Prediction from './pages/Prediction'
import PredictionHistory from './pages/PredictionHistory'
import PredictionAnalysis from './pages/PredictionAnalysis'
import ModelMonitoring from './pages/ModelMonitoring'
import Alerts from './pages/Alerts'
import AboutModel from './pages/AboutModel'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/prediction" element={<Prediction />} />
        <Route path="/history" element={<PredictionHistory />} />
        <Route path="/analysis" element={<PredictionAnalysis />} />
        <Route path="/monitoring" element={<ModelMonitoring />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/about" element={<AboutModel />} />
        <Route path="*" element={<Dashboard />} />
      </Route>
    </Routes>
  )
}
