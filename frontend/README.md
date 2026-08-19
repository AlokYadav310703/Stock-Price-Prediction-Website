# AAPL Prediction & Monitoring — Frontend

React + Vite + Tailwind frontend for the AAPL prediction/monitoring console. Currently runs entirely on **mock data** shaped exactly like the planned FastAPI responses, so wiring up the real backend later is a one-file change.

## Stack
- React 18 + Vite
- Tailwind CSS (custom "ink/paper/signal" token system — see `tailwind.config.js`)
- Recharts for charts
- React Router for the 7 pages
- Axios (wired up, unused until the backend exists)
- lucide-react for icons

## Pages
1. **Dashboard** (`/`) — overview: current price, next-day prediction, direction, accuracy, 30-day actual-vs-predicted chart, recent predictions table.
2. **Prediction** (`/prediction`) — full pipeline breakdown for the current prediction (Stage 1 ensemble, Stage 2 news correction, news/market inputs, similar historical events).
3. **Prediction History** (`/history`) — every stored prediction, filterable and paginated.
4. **Prediction Analysis** (`/analysis`) — actual-vs-predicted chart with 7D/30D/90D/1Y/All range selector, regression + directional metrics, correct/incorrect table.
5. **Model Monitoring** (`/monitoring`) — performance-over-time chart, prediction distribution, data quality checks, drift table, model health.
6. **Alerts** (`/alerts`) — severity-filterable alert feed.
7. **About Model** (`/about`) — architecture, features, training period, methodology, limitations.

## Run locally
```bash
npm install
cp .env.example .env
npm run dev
```
Opens on `http://localhost:5173`.

## Wiring up the real backend later
Everything goes through `src/services/api.js`. Each page calls `api.getX()` — it never imports mock data directly. To switch to the real FastAPI backend:

1. Set in `.env`:
   ```
   VITE_API_BASE_URL=https://your-backend-url/api
   VITE_USE_MOCK_DATA=false
   ```
2. Make sure your backend's response shapes match what `src/services/mockData.js` returns (field names are intentionally identical to the planned PostgreSQL `Prediction` model: `prediction_date`, `target_date`, `predicted_price`, `actual_price`, `predicted_direction`, `is_correct`, `absolute_error`, `percentage_error`, `model_version`, etc).
3. No page or component needs to change.

## Design notes
- Dark "terminal" theme by default (finance-terminal aesthetic), with a light/dark toggle in the sidebar.
- Tabular monospace numerals (IBM Plex Mono) for every price/metric; Inter for UI text/labels.
- Color is meaningful only: teal-green = correct/positive, red = incorrect/negative, amber = warning, indigo = the one interactive accent (active nav, primary chart series).
- Loading / error / empty states are implemented on every page (`components/ui.jsx`).
- Responsive: sidebar collapses to a drawer below `lg`, tables scroll horizontally on small screens.

## Deployment
Static build — deployable to any free static host (Vercel, Netlify, Cloudflare Pages, GitHub Pages):
```bash
npm run build   # outputs to dist/
```
