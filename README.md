# bot_trade

Bot en Python para BingX Futures con señales de tendencia para `BTC-USDT` y `ETH-USDT`.

> Importante: por seguridad, el modo por defecto es **paper**.

---

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

---

## 1) Cargar API keys

```bash
cp .env.example .env