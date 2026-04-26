from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    side: str | None
    reason: str
    entry_price: float | None = None
    tp_price: float | None = None
    sl_price: float | None = None


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




def _cross_in_last_n_bars(fast: pd.Series, slow: pd.Series, n: int, direction: str) -> bool:
    if len(fast) < n + 1 or len(slow) < n + 1:
        return False
    start = -1 - n
    f = fast.iloc[start:]
    s = slow.iloc[start:]
    for i in range(1, len(f)):
        prev_f, prev_s = f.iloc[i - 1], s.iloc[i - 1]
        curr_f, curr_s = f.iloc[i], s.iloc[i]
        if direction == "up" and prev_f <= prev_s and curr_f > curr_s:
            return True
        if direction == "down" and prev_f >= prev_s and curr_f < curr_s:
            return True
    return False


def build_exit_prices(entry_price: float, side: str, tp_pct: float, sl_pct: float) -> tuple[float, float]:
    if side == "long":
        tp_price = entry_price * (1 + tp_pct)
        sl_price = entry_price * (1 - sl_pct)
    else:
        tp_price = entry_price * (1 - tp_pct)
        sl_price = entry_price * (1 + sl_pct)
    return tp_price, sl_price


def generate_signal(df_entry: pd.DataFrame, df_trend: pd.DataFrame, params: dict) -> Signal:
    min_entry_rows = int(params.get("min_entry_rows", 60))
    min_trend_rows = int(params.get("min_trend_rows", 80))
    if len(df_entry) < min_entry_rows or len(df_trend) < min_trend_rows:
        return Signal(side=None, reason="insufficient_data")

    close_entry = df_entry["close"]
    close_trend = df_trend["close"]

    ema_fast_period = int(params.get("ema_fast", 9))
    ema_slow_period = int(params.get("ema_slow", 21))
    ema_trend_period = int(params.get("ema_trend", 50))
    rsi_period = int(params.get("rsi_period", 14))
    volume_ma_period = int(params.get("volume_ma_period", 20))

    tp_pct = float(params.get("take_profit_pct", 0.006))
    sl_pct = float(params.get("stop_loss_pct", 0.004))
    min_trend_gap_pct = float(params.get("min_trend_gap_pct", 0.0005))

    ema_fast = ema(close_entry, ema_fast_period)
    ema_slow = ema(close_entry, ema_slow_period)
    ema_trend = ema(close_trend, ema_trend_period)
    rsi_now = float(rsi(close_entry, rsi_period).iloc[-1])

    volume_ma = df_entry["volume"].rolling(volume_ma_period).mean()
    vol_ok = bool(df_entry["volume"].iloc[-1] > volume_ma.iloc[-1]) if pd.notna(volume_ma.iloc[-1]) else False

    trend_price = float(close_trend.iloc[-1])
    trend_ema_value = float(ema_trend.iloc[-1])
    trend_gap = abs(trend_price - trend_ema_value) / max(trend_price, 1e-12)

    trend_up = trend_price > trend_ema_value
    trend_down = trend_price < trend_ema_value
    trend_has_impulse = trend_gap >= min_trend_gap_pct

    trigger_mode = params.get("trigger_mode", "cross_or_alignment")
    cross_lookback = int(params.get("cross_lookback", 3))

    long_cross_now = ema_fast.iloc[-2] <= ema_slow.iloc[-2] and ema_fast.iloc[-1] > ema_slow.iloc[-1]
    short_cross_now = ema_fast.iloc[-2] >= ema_slow.iloc[-2] and ema_fast.iloc[-1] < ema_slow.iloc[-1]
    long_cross_recent = _cross_in_last_n_bars(ema_fast, ema_slow, cross_lookback, "up")
    short_cross_recent = _cross_in_last_n_bars(ema_fast, ema_slow, cross_lookback, "down")

    long_alignment = ema_fast.iloc[-1] > ema_slow.iloc[-1] and ema_fast.iloc[-1] >= ema_fast.iloc[-2]
    short_alignment = ema_fast.iloc[-1] < ema_slow.iloc[-1] and ema_fast.iloc[-1] <= ema_fast.iloc[-2]

    if trigger_mode == "cross_only":
        long_trigger = long_cross_now
        short_trigger = short_cross_now
    elif trigger_mode == "cross_recent":
        long_trigger = long_cross_recent
        short_trigger = short_cross_recent
    else:
        long_trigger = long_cross_recent or long_alignment
        short_trigger = short_cross_recent or short_alignment

    rsi_ok_long = rsi_now > float(params.get("rsi_long_threshold", 50))
    rsi_ok_short = rsi_now < float(params.get("rsi_short_threshold", 50))

    allow_countertrend_long = bool(params.get("allow_countertrend_long", False))
    allow_countertrend_short = bool(params.get("allow_countertrend_short", False))

    long_setup = (trend_up and trend_has_impulse) or (allow_countertrend_long and long_trigger)
    short_setup = (trend_down and trend_has_impulse) or (allow_countertrend_short and short_trigger)

    diagnostics = {
        "trend_up": bool(trend_up),
        "trend_down": bool(trend_down),
        "long_setup": bool(long_setup),
        "short_setup": bool(short_setup),
        "long_trigger": bool(long_trigger),
        "short_trigger": bool(short_trigger),
        "rsi": round(rsi_now, 2),
        "rsi_ok_long": bool(rsi_ok_long),
        "rsi_ok_short": bool(rsi_ok_short),
        "vol_ok": bool(vol_ok),
        "trend_gap_pct": round(trend_gap, 5),
        "trigger_mode": trigger_mode,
        "allow_countertrend_long": allow_countertrend_long,
        "allow_countertrend_short": allow_countertrend_short,
    }

    entry_price = float(close_entry.iloc[-1])

    if long_setup and long_trigger and rsi_ok_long and vol_ok:
        tp_price, sl_price = build_exit_prices(entry_price, "long", tp_pct, sl_pct)
        return Signal(
            side="long",
            reason=f"long_signal:{diagnostics}",
            entry_price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
        )

    if short_setup and short_trigger and rsi_ok_short and vol_ok:
        tp_price, sl_price = build_exit_prices(entry_price, "short", tp_pct, sl_pct)
        return Signal(
            side="short",
            reason=f"short_signal:{diagnostics}",
            entry_price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
        )

    return Signal(side=None, reason=f"no_signal:{diagnostics}")
