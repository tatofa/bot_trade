from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests


@dataclass
class BingXClient:
    api_key: str
    api_secret: str
    base_url: str = "https://open-api.bingx.com"

    def _sign(self, params: dict[str, Any]) -> str:
        query = urlencode(sorted(params.items()))
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

<<<<<<< codex/develop-btc-and-eth-trading-bot-xxj5jv
    def _ensure_success(self, payload: dict[str, Any], endpoint: str) -> dict[str, Any]:
        """Raise when BingX returns business-level error despite HTTP 200."""
        code = payload.get("code")
        if code in (0, "0", None):
            return payload
        msg = payload.get("msg") or payload.get("message") or "unknown_error"
        raise RuntimeError(f"BingX API error on {endpoint}: code={code} msg={msg}")

=======
>>>>>>> main
    def _request(self, method: str, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        headers = {"X-BX-APIKEY": self.api_key} if self.api_key else {}

        if self.api_key and self.api_secret:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)

        response = requests.request(method, f"{self.base_url}{endpoint}", params=params, headers=headers, timeout=15)
        response.raise_for_status()
<<<<<<< codex/develop-btc-and-eth-trading-bot-xxj5jv
        payload = response.json()
        return self._ensure_success(payload, endpoint)
=======
        return response.json()
>>>>>>> main

    def server_time(self) -> dict[str, Any]:
        return self._request("GET", "/openApi/swap/v2/server/time")

    def get_klines(self, symbol: str, interval: str = "15m", limit: int = 500) -> dict[str, Any]:
        return self._request(
            "GET",
            "/openApi/swap/v3/quote/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        position_side: str,
        order_type: str = "MARKET",
    ) -> dict[str, Any]:
        params = {
            "symbol": symbol,
            "side": side,
            "positionSide": position_side,
            "type": order_type,
            "quantity": f"{quantity:.6f}",
        }
<<<<<<< codex/develop-btc-and-eth-trading-bot-xxj5jv
        payload = self._request("POST", "/openApi/swap/v2/trade/order", params)
        data = payload.get("data", {}) if isinstance(payload.get("data", {}), dict) else {}
        # Optional safety check: if API accepted but no order id details, raise explicit error.
        if not any(k in data for k in ("orderId", "clientOrderId", "orderID")):
            raise RuntimeError(f"BingX order response missing order id: {payload}")
        return payload
=======
        return self._request("POST", "/openApi/swap/v2/trade/order", params)
>>>>>>> main
