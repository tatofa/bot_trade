from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PaperExecutor:
    positions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def open_position(self, symbol: str, side: str, qty: float, entry: float, stop: float, take_profit: float) -> None:
        self.positions[symbol] = {
            "side": side,
            "qty": qty,
            "entry": entry,
            "stop": stop,
            "take_profit": take_profit,
        }

    def close_position(self, symbol: str) -> None:
        self.positions.pop(symbol, None)
