import React, { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  Activity,
  History,
  LineChart,
  RadioTower,
  Bell,
  Info,
  Sun,
  Moon,
  Menu,
  X,
} from 'lucide-react'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { fmtUSD, fmtPct } from './ui'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/prediction', label: 'Prediction', icon: Activity },
  { to: '/history', label: 'Prediction History', icon: History },
  { to: '/analysis', label: 'Prediction Analysis', icon: LineChart },
  { to: '/monitoring', label: 'Model Monitoring', icon: RadioTower },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/about', label: 'About Model', icon: Info },
]

function TickerTape() {
  const { data } = useAsync(() => Promise.all([api.getStockSummary(), api.getLatestPrediction(), api.getPerformanceMetrics('90d'), api.getModelHealth()]), [])

  if (!data) return <div className="h-9 border-b border-ink-600 bg-ink-900" />

  const [stock, prediction, perf, health] = data
  const items = [
    `${stock.symbol} ${fmtUSD(stock.current_price)}`,
    `${fmtPct(stock.change_pct)} TODAY`,
    `NEXT-DAY TARGET ${fmtUSD(prediction.predicted_price)}`,
    `DIR ${prediction.predicted_direction}`,
    !perf.insufficient_data ? `DIR. ACCURACY ${perf.directional_accuracy}%` : 'DIR. ACCURACY —',
    !perf.insufficient_data ? `MAE ${perf.mae}` : 'MAE —',
    `MODEL ${health.model_version}`,
    `STATUS ${health.status.toUpperCase()}`,
  ]
  const loop = [...items, ...items]

  return (
    <div className="h-9 border-b border-ink-600 bg-ink-900 overflow-hidden flex items-center">
      <div className="flex whitespace-nowrap animate-ticker">
        {loop.map((item, i) => (
          <span key={i} className="num text-xs text-paper-dim px-4 border-r border-ink-600/70">
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function Layout() {
  const [theme, setTheme] = useState('dark')
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.classList.toggle('theme-light', theme === 'light')
  }, [theme])

  return (
    <div className="min-h-screen flex bg-ink-950">
      {/* Sidebar (desktop) */}
      <aside className="hidden lg:flex w-60 flex-shrink-0 flex-col border-r border-ink-600 bg-ink-900">
        <SidebarContent theme={theme} setTheme={setTheme} />
      </aside>

      {/* Sidebar (mobile drawer) */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="w-64 bg-ink-900 border-r border-ink-600 flex flex-col">
            <SidebarContent theme={theme} setTheme={setTheme} onNavigate={() => setMobileOpen(false)} />
          </div>
          <div className="flex-1 bg-black/60" onClick={() => setMobileOpen(false)} />
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="flex items-center gap-3 px-4 sm:px-6 h-14 border-b border-ink-600 bg-ink-950/80 backdrop-blur sticky top-0 z-30">
          <button className="lg:hidden text-paper-dim" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-signal-up animate-pulse" />
            <span className="text-xs text-paper-dim num">AAPL PREDICTION &amp; MONITORING CONSOLE</span>
          </div>
        </header>
        <TickerTape />
        <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function SidebarContent({ theme, setTheme, onNavigate }) {
  return (
    <>
      <div className="h-14 flex items-center gap-2 px-5 border-b border-ink-600">
        <div className="h-7 w-7 rounded-md bg-accent flex items-center justify-center text-ink-950 font-bold text-sm">A</div>
        <div className="leading-tight">
          <div className="text-sm font-semibold text-paper">AAPL Predictor</div>
          <div className="text-[10px] text-paper-dim uppercase tracking-wide">ML Console</div>
        </div>
        <button
          className="lg:hidden ml-auto text-paper-dim"
          onClick={onNavigate}
          aria-label="Close navigation"
        >
          <X size={18} />
        </button>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-accent-dim text-paper border border-accent/40'
                  : 'text-paper-dim hover:bg-ink-700 hover:text-paper border border-transparent'
              }`
            }
          >
            <Icon size={16} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-ink-600">
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="w-full flex items-center gap-2 justify-center rounded-lg px-3 py-2 text-xs font-medium text-paper-dim hover:bg-ink-700 hover:text-paper transition-colors"
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
          {theme === 'dark' ? 'Light mode' : 'Dark mode'}
        </button>
      </div>
    </>
  )
}
