# backtest_strategies.py
"""
Comparador de estrategias del proyecto.
Versión limpia: solo incluye MA_RSI_OPT.
Fácil de extender añadiendo más estrategias.
"""

import pandas as pd

from config.settings import BACKTEST_CONFIG, RISK_CONFIG
from data.downloader import get_datos_cripto_cached
from backtesting.engine import Backtester
from reporting.summary import print_backtest_summary

# Estrategia MA_RSI_OPT
from strategies.ma_rsi_strategy import (
    MovingAverageRSIStrategy,
    MovingAverageRSIStrategyConfig,
)

# ============================================================
# 1. CONFIGURACIÓN DE LA MEJOR VERSIÓN DE MA_RSI
# ============================================================

MA_RSI_OPT_CONFIG = MovingAverageRSIStrategyConfig(
    fast_window=10,
    slow_window=25,
    rsi_window=10,
    rsi_overbought=70.0,
    rsi_oversold=30.0,
    use_rsi_filter=False,
    signal_mode="cross",
    use_trend_filter=True,
    trend_ma_window=200,
)


def run_strategy(name: str, strategy_cls, cfg, df, backtest_config, risk_cfg):
    """
    Ejecuta una estrategia sobre un DataFrame.
    """
    strategy = strategy_cls(config=cfg)
    df_signals = strategy.generate_signals(df)

    backtester = Backtester(
        backtest_config=backtest_config,
        risk_config=risk_cfg,
    )
    result = backtester.run(df_signals)

    print(f"\n=== Backtest estrategia: {name} ===")
    print(f"BacktestConfig: sl_pct={backtest_config.sl_pct}, tp_rr={backtest_config.tp_rr}, "
          f"atr_mult_sl={backtest_config.atr_mult_sl}, atr_mult_tp={backtest_config.atr_mult_tp}")

    print_backtest_summary(result)

    return {
        "strategy": name,
        "num_trades": result.num_trades,
        "total_return_pct": result.total_return_pct,
        "max_drawdown_pct": result.max_drawdown_pct,
        "winrate_pct": result.winrate_pct,
        "profit_factor": result.profit_factor,
    }


def main():
    symbol = "BTC/USDT"
    timeframe = "15m"
    limit = 5000

    print(f"Obteniendo datos de {symbol} en timeframe {timeframe}...")
    df = get_datos_cripto_cached(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        force_download=False,
    )
    print(f"Filas obtenidas: {len(df)}")

    # ============================================================
    # 2. Ejecutar MA_RSI_OPT
    # ============================================================

    results = []

    res = run_strategy(
        name="MA_RSI_OPT",
        strategy_cls=MovingAverageRSIStrategy,
        cfg=MA_RSI_OPT_CONFIG,
        df=df,
        backtest_config=BACKTEST_CONFIG,
        risk_cfg=RISK_CONFIG,
    )
    results.append(res)

    # ============================================================
    # 3. Resumen comparativo (por si se añaden más estrategias)
    # ============================================================

    print("\n===== RESUMEN COMPARATIVO ESTRATEGIAS =====")
    df_summary = pd.DataFrame(results)
    df_summary = df_summary.sort_values(
        by="total_return_pct", ascending=False
    ).reset_index(drop=True)
    print(df_summary)

    print("\nFin del análisis.")


if __name__ == "__main__":
    main()