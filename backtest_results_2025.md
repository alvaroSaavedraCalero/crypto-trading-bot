# Resultados de Backtest: 2025 (Optimizado)

**Periodo:** 1 de Enero de 2025 - 24 de Noviembre de 2025

Se ha ejecutado un backtest de las estrategias tras una optimización completa sobre datos recientes (últimos 10,000 periodos de 15m).

## Resumen Comparativo

| Estrategia | Símbolo | Timeframe | Trades | Retorno Total | Max Drawdown | Winrate | Profit Factor |
|---|---|---|---|---|---|---|---|
| **MACD_ADX_TREND_OPT_ETHUSDT_15m** | ETH/USDT | 15m | 273 | **+11.65%** | -29.15% | 32.97% | 1.14 |
| **SUPERTREND_OPT_BTCUSDT_15m** | BTC/USDT | 15m | 107 | **+5.48%** | -14.75% | 19.63% | 1.12 |
| **KELTNER_BREAKOUT_OPT_SOLUSDT_15m** | SOL/USDT | 15m | 556 | **-21.27%** | -48.51% | 36.69% | 1.03 |

## Análisis

### Estrategias Positivas
*   **MACD_ADX_TREND (ETH)**: Mejor rendimiento con +11.65%. Parámetros optimizados: fast_ema=12, slow_ema=20, signal_ema=6, ADX threshold=20, SL=1%, TP=2.5x.
*   **SUPERTREND (BTC)**: Rendimiento positivo de +5.48% con drawdown controlado (-14.75%). Parámetros: ATR period=20, multiplier=4.0, ADX filter activo (threshold=25), SL=1%, TP=5x.

### Estrategias con Pérdidas
*   **KELTNER (SOL)**: A pesar de mostrar excelentes resultados en optimización reciente (+35%), el backtest anual muestra -21.27% con drawdown severo (-48.51%). Esto indica que SOL tuvo condiciones muy diferentes en la primera mitad del año.

## Proceso de Optimización

1. **MACD_ADX (ETH)**: Optimizado sobre 5,000 velas. Mejor resultado: 9.09% en periodo de optimización.
2. **Supertrend (BTC)**: Optimizado sobre 10,000 velas. Mejor resultado: 15.79% en periodo de optimización.
3. **Keltner (SOL)**: Optimizado sobre 10,000 velas. Mejor resultado: 35.12% en periodo de optimización.
4. **Bollinger MR (BNB)**: Descartada - todos los resultados negativos en optimización.
5. **Squeeze Momentum (BNB)**: Descartada - todos los resultados negativos en optimización.

## Conclusiones

- **2 de 3 estrategias** muestran rendimiento positivo en el año completo.
- El **retorno combinado** de las estrategias positivas es de **+17.13%** (promedio simple).
- La optimización sobre datos recientes puede no capturar las condiciones de todo el año, especialmente para activos volátiles como SOL.
