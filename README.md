# bot_trade

Bot base en Python para **paper trading** en BingX Futures con señales de tendencia para `BTCUSDT` y `ETHUSDT`.

## Estructura

- `main.py`: loop principal.
- `config.py`: carga `.env` + `config.yaml`.
- `exchange_bingx.py`: cliente HTTP para endpoints de BingX.
- `strategy.py`: EMA/RSI/ATR y señal long/short.
- `risk_manager.py`: sizing por riesgo y niveles SL/TP.
- `executor.py`: ejecutor paper (sin órdenes reales).
- `config.yaml`: parámetros iniciales.
- `.env.example`: variables de entorno.
- `railway.json` + `Procfile`: despliegue en Railway.

## Arranque local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Vincular a GitHub

Si este repo no tiene remoto aún:

```bash
git remote add origin <URL_DEL_REPO_GITHUB>
git push -u origin <TU_RAMA>
```

## Vincular y desplegar en Railway

1. En Railway: **New Project** → **Deploy from GitHub repo**.
2. Conecta tu cuenta de GitHub y selecciona este repositorio.
3. En Variables del servicio, agrega:
   - `BINGX_API_KEY`
   - `BINGX_API_SECRET`
   - `BOT_MODE=paper`
4. Railway detectará `railway.json` y usará `python main.py`.
5. Revisa logs del worker para confirmar que el loop corre.

## Nota de riesgo

Este proyecto es una base técnica y **no garantiza ganancias**. Antes de operar en real, ejecuta backtesting y paper trading prolongado.
