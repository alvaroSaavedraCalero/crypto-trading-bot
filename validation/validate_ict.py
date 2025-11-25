
import pandas as pd

from backtesting.engine import BacktestConfig, Backtester
from config.settings import RISK_CONFIG
from data.downloader import get_datos_cripto_cached
from strategies.ict_strategy import (
    ICTStrategy,
    ICTStrategyConfig,
)


def run_ict_on_market(
    symbol: str,
    timeframe: str,
    limit: int,
    cfg: ICTStrategyConfig,
    bt_cfg: BacktestConfig,
):
    print(f"\n=== ICT en {symbol} {timeframe} (limit={limit}) ===")

    df = get_datos_cripto_cached(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        force_download=False,
    )
    print(f"Filas obtenidas: {len(df)}")

    strategy = ICTStrategy(config=cfg)
    df_signals = strategy.generate_signals(df)

    bt = Backtester(
        backtest_config=bt_cfg,
        risk_config=RISK_CONFIG,
    )
    result = bt.run(df_signals)

    print("Número de trades:", result.num_trades)
    print(f"Retorno total: {result.total_return_pct:.2f} %")
    print(f"Max drawdown: {result.max_drawdown_pct:.2f} %")
    print(f"Winrate: {result.winrate_pct:.2f} %")
    print(f"Profit factor: {result.profit_factor:.2f}")

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "num_trades": result.num_trades,
        "total_return_pct": result.total_return_pct,
        "max_drawdown_pct": result.max_drawdown_pct,
        "winrate_pct": result.winrate_pct,
        "profit_factor": result.profit_factor,
    }


def main():
    # Valores óptimos obtenidos de opt_ict_BTCUSDT_15m.csv
    # kill_zone: 7-10 (London Open), swing_length=5, fvg_min_size_pct=0.05
    # sl_pct=0.02, tp_rr=4.0, allow_short=True

    ict_cfg = ICTStrategyConfig(
        kill_zone_start_hour=7,
        kill_zone_end_hour=10,
        swing_length=5,
        fvg_min_size_pct=0.05,
        allow_short=True,
    )

    bt_cfg = BacktestConfig(
        initial_capital=1000.0,
        sl_pct=0.02,     # 2% SL
        tp_rr=4.0,       # TP 1:4
        fee_pct=0.0005,
        allow_short=True,
    )

    markets = [
        ("BTC/USDT", "15m", 10000),
        ("ETH/USDT", "15m", 10000),
        ("BNB/USDT", "15m", 10000),
        ("SOL/USDT", "15m", 10000),
        ("XRP/USDT", "15m", 10000),
    ]

    rows = []
    for symbol, timeframe, limit in markets:
        row = run_ict_on_market(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            cfg=ict_cfg,
            bt_cfg=bt_cfg,
        )
        rows.append(row)

    print("\n===== RESUMEN VALIDACIÓN CRUZADA ICT =====")
    df_summary = pd.DataFrame(rows)
    df_summary = df_summary.sort_values(
        by="total_return_pct", ascending=False
    ).reset_index(drop=True)
    print(df_summary)


if __name__ == "__main__":
    main()
