from __future__ import annotations

import logging
import os
import time
from typing import Any

import pandas as pd

from config import load_config
from exchange_bingx import BingXClient
from executor import Executor, LiveExecutor, PaperExecutor
from risk_manager import position_size_usdt, stop_and_targets
from strategy import atr, generate_signal


def _resolve_log_level() -> int:
    name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    return getattr(logging, name, logging.INFO)


logging.basicConfig(level=_resolve_log_level(), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bot_trade")

LAST_SIGNAL_REASON: dict[str, str] = {}


def _normalize_symbol_candidates(symbol: str) -> list[str]:
    """Try common BingX symbol formats.

    Examples:
    - BTCUSDT -> BTC-USDT
    - ETH-USDT -> ETHUSDT
    """
    candidates = [symbol]
    if "-" in symbol:
        candidates.append(symbol.replace("-", ""))
    elif symbol.endswith("USDT"):
        candidates.append(symbol.replace("USDT", "-USDT"))
    return list(dict.fromkeys(candidates))


def klines_to_df(payload: dict[str, Any]) -> pd.DataFrame:
    rows = payload.get("data", [])
    if not rows:
        return pd.DataFrame()

    if isinstance(rows[0], dict):
        df = pd.DataFrame(rows)
        col_map = {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        }
    elif isinstance(rows[0], (list, tuple)) and len(rows[0]) >= 6:
        # Common exchange schema: [time, open, high, low, close, volume, ...]
        df = pd.DataFrame(rows)
        col_map = {1: "open", 2: "high", 3: "low", 4: "close", 5: "volume"}
    else:
        return pd.DataFrame()

    for source, target in col_map.items():
        if source not in df.columns:
            return pd.DataFrame()
        df[target] = pd.to_numeric(df[source], errors="coerce")

    return df[["open", "high", "low", "close", "volume"]].dropna()


def fetch_klines_with_fallback(
    client: BingXClient,
    symbol: str,
    interval: str,
    limit: int = 500,
) -> tuple[str, pd.DataFrame]:
    for candidate in _normalize_symbol_candidates(symbol):
        payload = client.get_klines(candidate, interval=interval, limit=limit)
        df = klines_to_df(payload)
        if not df.empty:
            return candidate, df
    return symbol, pd.DataFrame()


def run_once(client: BingXClient, executor: Executor, settings: dict) -> None:
    risk = settings["risk"]
    execution = settings["execution"]
    filters = settings["filters"]

    for symbol in settings.get("symbols", []):
        if executor.has_position(symbol):
            logger.info("%s skipped: already has position", symbol)
            continue

        resolved_symbol, df_15m = fetch_klines_with_fallback(
            client,
            symbol=symbol,
            interval=settings.get("entry_timeframe", settings.get("signal_timeframe", "1m")),
        )
        _, df_1h = fetch_klines_with_fallback(
            client,
            symbol=symbol,
            interval=settings.get("trend_timeframe", "5m"),
        )
        if df_15m.empty or df_1h.empty:
            logger.warning("%s skipped: no market data (check symbol format: BTC-USDT/ETH-USDT)", symbol)
            continue

        signal = generate_signal(df_15m, df_1h, {**filters, **execution})
        if not signal.side:
            previous_reason = LAST_SIGNAL_REASON.get(symbol)
            LAST_SIGNAL_REASON[symbol] = signal.reason
            if previous_reason != signal.reason:
                logger.info("%s no signal (%s)", symbol, signal.reason)
            else:
                logger.debug("%s no signal unchanged", symbol)
            continue

        current_price = float(signal.entry_price or df_15m["close"].iloc[-1])

        if signal.tp_price is not None and signal.sl_price is not None:
            stop_distance = abs(current_price - signal.sl_price)
            levels = {
                "stop_distance": stop_distance,
                "stop": float(signal.sl_price),
                "take_profit": float(signal.tp_price),
            }
        else:
            atr_value = float(atr(df_15m, 14).iloc[-1])
            levels = stop_and_targets(
                entry=current_price,
                atr_value=atr_value,
                side=signal.side,
                stop_mult=float(execution.get("stop_atr_mult", 1.5)),
                tp_r_final=float(execution.get("final_tp_r", 2.0)),
            )

        qty = position_size_usdt(
            account_size=float(risk.get("account_size_usdt", 1000)),
            risk_per_trade=float(risk.get("risk_per_trade", 0.0075)),
            stop_distance=levels["stop_distance"],
        )
        if qty <= 0:
            logger.warning("%s skipped: invalid qty", symbol)
            continue

        executor.open_position(symbol, signal.side, qty, current_price, levels["stop"], levels["take_profit"])
        LAST_SIGNAL_REASON.pop(symbol, None)
        logger.info(
            "%s opened %s qty=%.4f entry=%.2f stop=%.2f tp=%.2f source_symbol=%s",
            symbol,
            signal.side,
            qty,
            current_price,
            levels["stop"],
            levels["take_profit"],
            resolved_symbol,
        )


def main() -> None:
    cfg = load_config()
    client = BingXClient(api_key=cfg.api_key, api_secret=cfg.api_secret)
    if cfg.mode == "live":
        if not cfg.live_enabled:
            logger.warning(
                "Live mode requested but ENABLE_LIVE_TRADING is '%s' (must be true). Falling back to paper mode.",
                cfg.live_enabled_raw or "<empty>",
            )
            executor = PaperExecutor()
            cfg.mode = "paper"
        elif not cfg.api_key or not cfg.api_secret:
            logger.warning(
                "Live mode requested but missing API credentials. Falling back to paper mode."
            )
            executor = PaperExecutor()
            cfg.mode = "paper"
        else:
            executor = LiveExecutor(client=client)
    else:
        executor = PaperExecutor()

    logger.info("Bot started in %s mode", cfg.mode)
    while True:
        try:
            run_once(client, executor, cfg.settings)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Loop failed: %s", exc)
        time.sleep(30)


if __name__ == "__main__":
    main()
