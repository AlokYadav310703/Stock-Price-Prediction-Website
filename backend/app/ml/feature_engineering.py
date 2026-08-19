"""
Market data fetching + feature engineering.

Ported directly from the Streamlit app's fetch_apple_ohlc / compute_market_returns
functions, with the same defensive validation (empty response, too-few-rows,
NaN OHLC values) — that validation is exactly what prevents "$nan" predictions
and silent monitoring corruption, so it's preserved unchanged.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

from app.ml.exceptions import MarketDataError

logger = logging.getLogger("app.ml.feature_engineering")

OHLC_COLS = ["open", "high", "low", "close"]


def fetch_ohlc(symbol: str, lookback: int = 30) -> pd.DataFrame:
    """Fetch OHLC data for `symbol` and validate it before returning.

    Raises MarketDataError with a specific, actionable message for every
    failure mode instead of letting NaNs/empty frames flow downstream.
    """
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover
        raise MarketDataError("yfinance is not installed in this environment.") from exc

    df = yf.download(symbol, period="6mo", progress=False)

    if df is None or df.empty:
        raise MarketDataError(
            f"No price data available for {symbol}. Yahoo Finance returned an empty "
            "response — the provider may be down, rate-limiting, or the feed hasn't "
            "updated yet."
        )

    df = df.tail(lookback + 20).reset_index()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]

    if len(df) < 20:
        raise MarketDataError(
            f"Not enough price history for {symbol}: only {len(df)} row(s) returned, "
            "at least 20 are needed for technical indicators."
        )

    missing_cols = [c for c in OHLC_COLS if c not in df.columns]
    if missing_cols:
        raise MarketDataError(f"Malformed price data: missing columns {missing_cols}.")

    if df[OHLC_COLS].isnull().values.any():
        bad_rows = df[df[OHLC_COLS].isnull().any(axis=1)]
        bad_dates = bad_rows["date"].dt.date.astype(str).tolist() if "date" in bad_rows.columns else []
        raise MarketDataError(
            f"Incomplete OHLC data (NaN values) for {symbol}. Affected date(s): "
            f"{', '.join(bad_dates) or 'unknown'}."
        )

    if df.iloc[-1][OHLC_COLS].isnull().any():
        raise MarketDataError(f"Today's {symbol} price is unavailable (NaN).")

    return df


def compute_market_returns(df: pd.DataFrame) -> dict:
    closes = df["close"].values.astype(float)
    if len(closes) < 6 or np.isnan(closes[-1]) or np.isnan(closes[-2]) or np.isnan(closes[-6]):
        raise MarketDataError("Cannot compute market returns: insufficient or NaN closing prices.")
    return_1d = (closes[-1] - closes[-2]) / closes[-2]
    return_5d = (closes[-1] - closes[-6]) / closes[-6]
    return {"return_1d": float(return_1d), "return_5d": float(return_5d)}


def compute_rsi(closes: np.ndarray, period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    deltas = np.diff(closes[-(period + 1):])
    gains = deltas[deltas > 0].sum() / period
    losses = -deltas[deltas < 0].sum() / period
    if losses == 0:
        return 100.0
    rs = gains / losses
    return float(100 - (100 / (1 + rs)))


def compute_macd(closes: np.ndarray, fast: int = 12, slow: int = 26) -> Optional[float]:
    if len(closes) < slow:
        return None
    series = pd.Series(closes)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = (ema_fast - ema_slow).iloc[-1]
    return float(macd)


def compute_atr(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    if len(df) < period + 1:
        return None
    high, low, close = df["high"].values, df["low"].values, df["close"].values
    tr = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
    return float(np.mean(tr[-period:]))


def compute_momentum(closes: np.ndarray, period: int = 10) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    return float(closes[-1] - closes[-1 - period])


def compute_technical_indicators(df: pd.DataFrame) -> dict:
    """Compute the indicator set used both by the model and by drift monitoring."""
    closes = df["close"].values.astype(float)
    return {
        "rsi": compute_rsi(closes),
        "macd": compute_macd(closes),
        "atr": compute_atr(df),
        "momentum": compute_momentum(closes),
        "volume": float(df["volume"].iloc[-1]) if "volume" in df.columns else None,
    }
