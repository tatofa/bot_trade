# bot_trade

Bot en Python para BingX Futures con señales de tendencia para `BTC-USDT` y `ETH-USDT`.

> Importante: por seguridad, el modo por defecto es **paper**.

## Estructura

- `run_bot.py`: preflight (detecta conflictos de merge) + arranque.
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
python run_bot.py
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
   - `LOG_LEVEL` (`INFO`, `WARNING`, `ERROR`, `DEBUG`)
4. Railway usará `python run_bot.py`.

## Estado actual de ejecución real

- `BOT_MODE=live` habilita modo live.
- Si faltan keys en live, el bot hace fallback automático a `paper` y deja warning en logs.
- `LOG_LEVEL` solo controla verbosidad.

## Ajuste de señales (scalping)

En `config.yaml` puedes ajustar:
- `entry_timeframe` y `trend_timeframe`.
- `filters.ema_fast` / `filters.ema_slow`.
- `filters.trigger_mode`: `cross_only`, `cross_recent` o `cross_or_alignment` (menos estricto).
- `filters.cross_lookback`: cuántas velas atrás buscar cruce reciente.
- `filters.ema_trend` y `filters.min_trend_gap_pct`.
- `filters.require_volume_confirmation`.
- `filters.rsi_long_threshold` / `filters.rsi_short_threshold`.
- `execution.take_profit_pct` / `execution.stop_loss_pct`.

## Errores comunes

- `no market data`: revisa símbolo (`BTC-USDT` / `ETH-USDT`), el bot también intenta fallback a `BTCUSDT`.
- `signature/auth`: revisa API key/secret, permisos de futuros, y que no haya espacios extra en variables de entorno. El cliente reintenta una firma alternativa si recibe `code=100001`.
- `order failed`: revisa permisos de API de futures, modo hedge/one-way y precisión mínima de cantidad.
- `Insufficient margin`: baja `risk_per_trade`, sube `stop_loss_pct`, o ajusta `risk.max_margin_usage`.
- `merge conflict markers detected`: tu imagen fue construida con archivos en conflicto; redeploy desde el último commit limpio.

## Build safety

- El build del contenedor valida marcadores de conflicto y también compila `*.py` para cortar errores de sintaxis/indentación antes de deploy.

## Nota de riesgo


Este proyecto **no garantiza ganancias**. Haz backtesting y paper trading antes de operar en real.


## Perfil operativo rápido (40 USDT)

Valores iniciales sugeridos para empezar a operar con cuenta pequeña:
- `risk.account_size_usdt: 40`
- `execution.leverage.BTC-USDT: 10`
- `execution.leverage.ETH-USDT: 10`
- `risk.max_margin_usage: 0.95`
- `filters.require_volume_confirmation: false`
- `filters.rsi_long_threshold: 45` / `filters.rsi_short_threshold: 55`
- `filters.trigger_mode: cross_or_alignment` con `cross_lookback: 5`

> Ajusta en vivo con cuidado; 10x es el máximo recomendado en esta plantilla.
