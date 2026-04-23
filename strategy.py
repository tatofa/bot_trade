from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    side: str | None
    reason: str


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(com=period - 1, adjust=False).mean()
    ma_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, 1e-12)
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def generate_signal(df_15m: pd.DataFrame, df_1h: pd.DataFrame, params: dict) -> Signal:
    if len(df_15m) < 60 or len(df_1h) < 220:
        return Signal(side=None, reason="insufficient_data")

    close_15 = df_15m["close"]
    close_1h = df_1h["close"]

    ema20 = ema(close_15, 20)
    ema50 = ema(close_15, 50)
    ema200_1h = ema(close_1h, 200)
    rsi14 = rsi(close_15, 14)
    vol_ma = df_15m["volume"].rolling(params.get("volume_ma_period", 20)).mean()

    cross_up = ema20.iloc[-2] <= ema50.iloc[-2] and ema20.iloc[-1] > ema50.iloc[-1]
    cross_down = ema20.iloc[-2] >= ema50.iloc[-2] and ema20.iloc[-1] < ema50.iloc[-1]

    trend_up = close_1h.iloc[-1] > ema200_1h.iloc[-1]
    trend_down = close_1h.iloc[-1] < ema200_1h.iloc[-1]

    rsi_now = rsi14.iloc[-1]
    vol_ok = df_15m["volume"].iloc[-1] > vol_ma.iloc[-1]

    long_ok = (
        trend_up
        and cross_up
        and params.get("rsi_long_min", 50) <= rsi_now <= params.get("rsi_long_max", 68)
        and vol_ok
    )
    short_ok = (
        trend_down
        and cross_down
        and params.get("rsi_short_min", 32) <= rsi_now <= params.get("rsi_short_max", 50)
        and vol_ok
    )

    if long_ok:
        return Signal(side="long", reason="trend_ema_cross_rsi_volume")
    if short_ok:
        return Signal(side="short", reason="trend_ema_cross_rsi_volume")
    return Signal(side=None, reason="no_signal")
