import pandas as pd

from backtesting.engine import BacktestConfig, Backtester
from config.settings import RISK_CONFIG
from data.downloader import get_datos_cripto_cached
from strategies.keltner_breakout_strategy import (
    KeltnerBreakoutStrategy,
    KeltnerBreakoutStrategyConfig,
)


def run_keltner_on_market(
    symbol: str,
    timeframe: str,
    limit: int,
    cfg: KeltnerBreakoutStrategyConfig,
    bt_cfg: BacktestConfig,
):
    print(f"\n=== KELTNER en {symbol} {timeframe} (limit={limit}) ===")

    df = get_datos_cripto_cached(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        force_download=False,
    )
    print(f"Filas obtenidas: {len(df)}")

    strategy = KeltnerBreakoutStrategy(config=cfg)
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
    # Valores óptimos obtenidos de opt_keltner_SOLUSDT_15m.csv
    keltner_cfg = KeltnerBreakoutStrategyConfig(
        kc_window=30,
        kc_mult=2.5,
        atr_window=20,
        atr_min_percentile=0.4,
        use_trend_filter=False,
        trend_ema_window=100,
        allow_short=True,
        side_mode="both",
    )

    bt_cfg = BacktestConfig(
        initial_capital=1000.0,
        sl_pct=0.0075,   # 0.75% SL
        tp_rr=2.0,       # TP 1:2
        fee_pct=0.0005,
        allow_short=True,
    )

    markets = [
        ("SOL/USDT", "15m", 10000),
        ("BTC/USDT", "15m", 10000),
        ("ETH/USDT", "15m", 10000),
        ("BNB/USDT", "15m", 10000),
        ("XRP/USDT", "15m", 10000),
        ("SOL/USDT", "1h",  5000),
    ]

    rows = []
    for symbol, timeframe, limit in markets:
        row = run_keltner_on_market(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            cfg=keltner_cfg,
            bt_cfg=bt_cfg,
        )
        rows.append(row)

    print("\n===== RESUMEN VALIDACIÓN CRUZADA KELTNER =====")
    df_summary = pd.DataFrame(rows)
    df_summary = df_summary.sort_values(
        by="total_return_pct", ascending=False
    ).reset_index(drop=True)
    print(df_summary)


if __name__ == "__main__":
    main()
