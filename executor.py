from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

from exchange_bingx import BingXClient

logger = logging.getLogger("bot_trade")


class Executor(Protocol):
    def has_position(self, symbol: str) -> bool: ...

    def open_position(self, symbol: str, side: str, qty: float, entry: float, stop: float, take_profit: float) -> None: ...


@dataclass
class PaperExecutor:
    positions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def open_position(self, symbol: str, side: str, qty: float, entry: float, stop: float, take_profit: float) -> None:
        self.positions[symbol] = {
            "mode": "paper",
            "side": side,
            "qty": qty,
            "entry": entry,
            "stop": stop,
            "take_profit": take_profit,
        }

    def close_position(self, symbol: str) -> None:
        self.positions.pop(symbol, None)


@dataclass
class LiveExecutor:
    client: BingXClient
    execution_config: dict[str, Any]
    positions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def _leverage_for_symbol(self, symbol: str) -> int:
        raw = self.execution_config.get("leverage", {}).get(symbol)
        if raw is None and "-" in symbol:
            raw = self.execution_config.get("leverage", {}).get(symbol.replace("-", ""))
        if raw is None:
            return 1
        leverage = int(raw)
        if leverage > 10:
            raise RuntimeError(f"Configured leverage too high for safety: {symbol}={leverage}x")
        return leverage

    def _configure_symbol(self, symbol: str, side: str, leverage: int) -> None:
        margin_mode = str(self.execution_config.get("margin_mode", "isolated"))
        logger.info("%s configuring margin_mode=%s leverage=%sx", symbol, margin_mode, leverage)

        self.client.set_margin_mode(symbol, margin_mode)
        logger.info("%s margin mode configured", symbol)

        # configure leverage for both sides to support hedge-mode accounts
        self.client.set_leverage(symbol, leverage, side="LONG")
        self.client.set_leverage(symbol, leverage, side="SHORT")
        logger.info("%s leverage configured to %sx", symbol, leverage)

    def open_position(self, symbol: str, side: str, qty: float, entry: float, stop: float, take_profit: float) -> None:
        order_side = "BUY" if side == "long" else "SELL"
        position_side = "LONG" if side == "long" else "SHORT"
        leverage = self._leverage_for_symbol(symbol)

        try:
            self._configure_symbol(symbol, side, leverage)
        except Exception as exc:  # noqa: BLE001
            logger.error("%s failed to configure leverage/margin; order skipped: %s", symbol, exc)
            raise

        logger.info("%s placing order side=%s qty=%.6f", symbol, side, qty)
        order = self.client.place_order(
            symbol=symbol,
            side=order_side,
            quantity=qty,
            position_side=position_side,
            order_type="MARKET",
        )

        self.positions[symbol] = {
            "mode": "live",
            "side": side,
            "qty": qty,
            "entry": entry,
            "stop": stop,
            "take_profit": take_profit,
            "exchange_order": order,
        }
