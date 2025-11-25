# scripts/backtest_forex.py

"""
Backtest script for Forex strategies.
Similar to backtest_strategies.py but uses Forex data source.
"""

from config.settings import (
    FOREX_STRATEGIES,
    MarketType,
    RISK_CONFIG,
)
from data.forex_data import get_forex_data
from backtesting.engine import Backtester
from reporting.summary import print_backtest_summary, save_equity_plot
from strategies.registry import create_strategy


def run_backtest_forex(run_cfg):
    """
    Ejecuta backtest para una configuración de estrategia Forex.
    """
    print(f"\n=== Backtest Forex: {run_cfg.name} ({run_cfg.strategy_type}) ===")
    print(f"Símbolo: {run_cfg.symbol}, timeframe: {run_cfg.timeframe}, límite velas: {run_cfg.limit_candles}")
    
    # Descargar datos de Forex
    df = get_forex_data(
        symbol=run_cfg.symbol,
        timeframe=run_cfg.timeframe,
        limit=run_cfg.limit_candles,
        force_download=False,
    )
    print(f"Filas obtenidas: {len(df)}")
    
    # Crear estrategia
    strategy = create_strategy(
        strategy_type=run_cfg.strategy_type,
        config_obj=run_cfg.strategy_config,
    )
    
    # Generar señales
    df_signals = strategy.generate_signals(df)
    
    # Ejecutar backtest
    backtester = Backtester(
        backtest_config=run_cfg.backtest_config,
        risk_config=RISK_CONFIG,
    )
    result = backtester.run(df_signals)
    
    print_backtest_summary(result)
    
    # Generar gráfico de equity curve
    save_equity_plot(result, title=f"{run_cfg.name}")
    
    return {
        "strategy": run_cfg.name,
        "symbol": run_cfg.symbol,
        "timeframe": run_cfg.timeframe,
        "num_trades": result.num_trades,
        "total_return_pct": result.total_return_pct,
        "max_drawdown_pct": result.max_drawdown_pct,
        "winrate_pct": result.winrate_pct,
        "profit_factor": result.profit_factor,
    }


def main():
    import pandas as pd
    
    print("=" * 60)
    print("BACKTEST DE ESTRATEGIAS FOREX")
    print("=" * 60)
    
    rows = []
    for run_cfg in FOREX_STRATEGIES:
        try:
            row = run_backtest_forex(run_cfg)
            rows.append(row)
        except Exception as e:
            print(f"\n✗ Error en {run_cfg.name}: {e}")
            import traceback
            traceback.print_exc()
    
    if rows:
        print("\n===== RESUMEN COMPARATIVO ESTRATEGIAS FOREX =====")
        df_summary = pd.DataFrame(rows)
        df_summary = df_summary.sort_values(
            by="total_return_pct", ascending=False
        ).reset_index(drop=True)
        print(df_summary)
    else:
        print("\n⚠ No se completaron backtests exitosos")


if __name__ == "__main__":
    main()
