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
    settings: dict[str, Any]


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

    return RuntimeConfig(mode=mode, api_key=api_key, api_secret=api_secret, settings=settings)
