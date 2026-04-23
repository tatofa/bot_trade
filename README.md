# bot_trade

Bot base en Python para **paper trading** en BingX Futures con señales de tendencia para `BTC-USDT` y `ETH-USDT`.

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

## 1) Cargar API keys

Crea tu `.env` local desde el ejemplo:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales reales:

```env
BINGX_API_KEY=TU_API_KEY
BINGX_API_SECRET=TU_API_SECRET
BOT_MODE=paper
```

> Nota: para endpoint público de velas, a veces funciona sin key; para operar real necesitas keys activas.

## 2) Arranque local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 3) Subir al repo de GitHub

Si este repo no tiene remoto aún:

```bash
git remote add origin <URL_DEL_REPO_GITHUB>
git push -u origin <TU_RAMA>
```

## 4) Vincular y desplegar en Railway

1. En Railway: **New Project** → **Deploy from GitHub repo**.
2. Conecta tu cuenta de GitHub y selecciona este repositorio.
3. En Variables del servicio, agrega:
   - `BINGX_API_KEY`
   - `BINGX_API_SECRET`
   - `BOT_MODE=paper`
4. Railway detectará `railway.json` y usará `python main.py`.
5. Revisa logs del worker para confirmar que el loop corre.

## Errores comunes

- `no market data`: revisa formato de símbolo (`BTC-USDT`/`ETH-USDT`).
- `signature` o `auth`: revisa API key/secret y permisos en BingX.

## Nota de riesgo

Este proyecto es una base técnica y **no garantiza ganancias**. Antes de operar en real, ejecuta backtesting y paper trading prolongado.
