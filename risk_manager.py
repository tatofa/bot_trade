from __future__ import annotations


def position_size_usdt(account_size: float, risk_per_trade: float, stop_distance: float) -> float:
    if stop_distance <= 0:
        return 0.0
    return (account_size * risk_per_trade) / stop_distance


def stop_and_targets(entry: float, atr_value: float, side: str, stop_mult: float, tp_r_final: float) -> dict:
    stop_distance = max(atr_value * stop_mult, 1e-8)

    if side == "long":
        stop = entry - stop_distance
        take_profit = entry + (stop_distance * tp_r_final)
    else:
        stop = entry + stop_distance
        take_profit = entry - (stop_distance * tp_r_final)

    return {
        "stop_distance": stop_distance,
        "stop": stop,
        "take_profit": take_profit,
    }
