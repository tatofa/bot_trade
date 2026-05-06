from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from exchange_bingx import BingXClient


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
    positions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def open_position(self, symbol: str, side: str, qty: float, entry: float, stop: float, take_profit: float) -> None:
        order_side = "BUY" if side == "long" else "SELL"
        position_side = "LONG" if side == "long" else "SHORT"

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
