from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class RuntimeConfig:
    mode: str
    api_key: str
    api_secret: str
    live_enabled: bool
    live_enabled_raw: str
    settings: dict[str, Any]


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized == "":
        return default
    return normalized in {"1", "true", "yes", "y", "on"}


def load_config(config_path: str = "config.yaml") -> RuntimeConfig:
    load_dotenv()
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with path.open("r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    mode = os.getenv("BOT_MODE", settings.get("mode", "paper"))
    api_key = os.getenv("BINGX_API_KEY", "")
    api_secret = os.getenv("BINGX_API_SECRET", "")
    live_enabled_raw = os.getenv("ENABLE_LIVE_TRADING", "")
    # If BOT_MODE=live and ENABLE_LIVE_TRADING is omitted, assume enabled for smoother Railway setup.
    live_enabled_default = mode.strip().lower() == "live"
    live_enabled = _as_bool(live_enabled_raw, default=live_enabled_default)

    return RuntimeConfig(
        mode=mode,
        api_key=api_key,
        api_secret=api_secret,
        live_enabled=live_enabled,
        live_enabled_raw=live_enabled_raw,
        settings=settings,
    )
