from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    side: str | None
    reason: str
<<<<<<< codex/develop-btc-and-eth-trading-bot-n6yp5q
    entry_price: float | None = None
    tp_price: float | None = None
    sl_price: float | None = None
=======
>>>>>>> main


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


<<<<<<< codex/develop-btc-and-eth-trading-bot-n6yp5q
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

    long_trigger = ema_fast.iloc[-2] <= ema_slow.iloc[-2] and ema_fast.iloc[-1] > ema_slow.iloc[-1]
    short_trigger = ema_fast.iloc[-2] >= ema_slow.iloc[-2] and ema_fast.iloc[-1] < ema_slow.iloc[-1]

    rsi_ok_long = rsi_now > float(params.get("rsi_long_threshold", 50))
    rsi_ok_short = rsi_now < float(params.get("rsi_short_threshold", 50))

    long_setup = trend_up and trend_has_impulse
    short_setup = trend_down and trend_has_impulse
=======
def generate_signal(df_15m: pd.DataFrame, df_1h: pd.DataFrame, params: dict) -> Signal:
    if len(df_15m) < 60 or len(df_1h) < 220:
        return Signal(side=None, reason="insufficient_data")

    close_15 = df_15m["close"]
    close_1h = df_1h["close"]

    ema20 = ema(close_15, 20)
    ema50 = ema(close_15, 50)
    ema200_1h = ema(close_1h, 200)
    rsi14 = rsi(close_15, 14)

    volume_period = int(params.get("volume_ma_period", 20))
    vol_ma = df_15m["volume"].rolling(volume_period).mean()

    # Strict crossing entry
    cross_up = ema20.iloc[-2] <= ema50.iloc[-2] and ema20.iloc[-1] > ema50.iloc[-1]
    cross_down = ema20.iloc[-2] >= ema50.iloc[-2] and ema20.iloc[-1] < ema50.iloc[-1]

    # Continuation entry (more frequent than a strict cross)
    trend_15m_up = ema20.iloc[-1] > ema50.iloc[-1]
    trend_15m_down = ema20.iloc[-1] < ema50.iloc[-1]

    trend_up = close_1h.iloc[-1] > ema200_1h.iloc[-1]
    trend_down = close_1h.iloc[-1] < ema200_1h.iloc[-1]

    rsi_now = float(rsi14.iloc[-1])
    require_volume = bool(params.get("require_volume_confirmation", False))
    vol_ok = bool(df_15m["volume"].iloc[-1] > vol_ma.iloc[-1]) if pd.notna(vol_ma.iloc[-1]) else False
    if not require_volume:
        vol_ok = True

    entry_mode = params.get("entry_mode", "cross_or_trend")
    long_trigger = cross_up if entry_mode == "cross_only" else (cross_up or trend_15m_up)
    short_trigger = cross_down if entry_mode == "cross_only" else (cross_down or trend_15m_down)

    long_ok = (
        trend_up
        and long_trigger
        and params.get("rsi_long_min", 45) <= rsi_now <= params.get("rsi_long_max", 75)
        and vol_ok
    )
    short_ok = (
        trend_down
        and short_trigger
        and params.get("rsi_short_min", 25) <= rsi_now <= params.get("rsi_short_max", 55)
        and vol_ok
    )

    if long_ok:
        return Signal(side="long", reason=f"long:{entry_mode}:rsi={rsi_now:.1f}")
    if short_ok:
        return Signal(side="short", reason=f"short:{entry_mode}:rsi={rsi_now:.1f}")
>>>>>>> main

    diagnostics = {
        "trend_up": bool(trend_up),
        "trend_down": bool(trend_down),
<<<<<<< codex/develop-btc-and-eth-trading-bot-n6yp5q
        "long_setup": bool(long_setup),
        "short_setup": bool(short_setup),
        "long_trigger": bool(long_trigger),
        "short_trigger": bool(short_trigger),
        "rsi": round(rsi_now, 2),
        "rsi_ok_long": bool(rsi_ok_long),
        "rsi_ok_short": bool(rsi_ok_short),
        "vol_ok": bool(vol_ok),
        "trend_gap_pct": round(trend_gap, 5),
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

=======
        "long_trigger": bool(long_trigger),
        "short_trigger": bool(short_trigger),
        "vol_ok": bool(vol_ok),
        "rsi": round(rsi_now, 1),
    }
>>>>>>> main
    return Signal(side=None, reason=f"no_signal:{diagnostics}")
