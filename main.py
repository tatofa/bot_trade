from __future__ import annotations

import logging
import time

import pandas as pd

from config import load_config
from exchange_bingx import BingXClient
from executor import PaperExecutor
from risk_manager import position_size_usdt, stop_and_targets
from strategy import atr, generate_signal


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bot_trade")


def klines_to_df(payload: dict) -> pd.DataFrame:
    rows = payload.get("data", [])
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    col_map = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }
    for source, target in col_map.items():
        df[target] = pd.to_numeric(df[source], errors="coerce")
    return df[["open", "high", "low", "close", "volume"]].dropna()


def run_once(client: BingXClient, paper: PaperExecutor, settings: dict) -> None:
    risk = settings["risk"]
    execution = settings["execution"]
    filters = settings["filters"]

    for symbol in settings.get("symbols", []):
        if paper.has_position(symbol):
            logger.info("%s skipped: already has position", symbol)
            continue

        df_15m = klines_to_df(client.get_klines(symbol, settings.get("signal_timeframe", "15m")))
        df_1h = klines_to_df(client.get_klines(symbol, settings.get("trend_timeframe", "1h")))
        if df_15m.empty or df_1h.empty:
            logger.warning("%s skipped: no market data", symbol)
            continue

        signal = generate_signal(df_15m, df_1h, filters)
        if not signal.side:
            logger.info("%s no signal (%s)", symbol, signal.reason)
            continue

        current_price = float(df_15m["close"].iloc[-1])
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

        paper.open_position(symbol, signal.side, qty, current_price, levels["stop"], levels["take_profit"])
        logger.info(
            "%s opened %s qty=%.4f entry=%.2f stop=%.2f tp=%.2f",
            symbol,
            signal.side,
            qty,
            current_price,
            levels["stop"],
            levels["take_profit"],
        )


def main() -> None:
    cfg = load_config()
    client = BingXClient(api_key=cfg.api_key, api_secret=cfg.api_secret)
    paper = PaperExecutor()

    logger.info("Bot started in %s mode", cfg.mode)
    while True:
        try:
            run_once(client, paper, cfg.settings)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Loop failed: %s", exc)
        time.sleep(30)


if __name__ == "__main__":
    main()
