# bot_trade

Bot en Python para BingX Futures con señales de tendencia para `BTC-USDT` y `ETH-USDT`.

> Importante: por seguridad, el modo por defecto es **paper**. Para ejecutar órdenes reales debes activar explícitamente `BOT_MODE=live` y `ENABLE_LIVE_TRADING=true`.

## Estructura

- `main.py`: loop principal.
- `config.py`: carga `.env` + `config.yaml`.
- `exchange_bingx.py`: cliente HTTP para BingX (market data + orden market).
- `strategy.py`: EMA/RSI/ATR y señal long/short.
- `risk_manager.py`: sizing por riesgo y niveles SL/TP.
- `executor.py`: ejecutor paper y ejecutor live.
- `config.yaml`: parámetros iniciales.
- `.env.example`: variables de entorno.
- `railway.json` + `Procfile`: despliegue en Railway.

## 1) Cargar API keys

```bash
cp .env.example .env
```

Edita `.env`:

```env
BINGX_API_KEY=TU_API_KEY
BINGX_API_SECRET=TU_API_SECRET

# paper (default)
BOT_MODE=paper
ENABLE_LIVE_TRADING=false

# live (real)
# BOT_MODE=live
# ENABLE_LIVE_TRADING=true
```

## 2) Arranque local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 3) Subir al repo de GitHub

```bash
git remote add origin <URL_DEL_REPO_GITHUB>
git push -u origin <TU_RAMA>
```

## 4) Vincular Railway

1. Railway → **New Project** → **Deploy from GitHub repo**.
2. Selecciona este repositorio.
3. En Variables del servicio, agrega:
   - `BINGX_API_KEY`
   - `BINGX_API_SECRET`
   - `BOT_MODE` (`paper` o `live`)
   - `ENABLE_LIVE_TRADING` (`false` o `true`)
4. Railway usará `python main.py`.

## Estado actual de ejecución real

- ✅ En `paper`: simula entradas internamente.
- ✅ En `live`: envía **orden market de entrada** vía API (`/openApi/swap/v2/trade/order`).
- ⚠️ Aún falta cablear en exchange las órdenes de SL/TP/trailing como órdenes nativas separadas.

## Errores comunes

- `no market data`: revisa símbolo (`BTC-USDT` / `ETH-USDT`), el bot también intenta fallback a `BTCUSDT`.
- `Live mode blocked`: activa `ENABLE_LIVE_TRADING=true` además de `BOT_MODE=live`.
- `signature/auth`: revisa API key/secret y permisos de futuros en BingX.

## Nota de riesgo

Este proyecto **no garantiza ganancias**. Haz backtesting y paper trading antes de operar en real.
