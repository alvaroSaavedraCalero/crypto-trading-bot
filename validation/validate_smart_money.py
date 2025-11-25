
import pandas as pd

from backtesting.engine import BacktestConfig, Backtester
from config.settings import RISK_CONFIG
from data.downloader import get_datos_cripto_cached
from strategies.smart_money_strategy import (
    SmartMoneyStrategy,
    SmartMoneyStrategyConfig,
)


def run_smart_money_on_market(
    symbol: str,
    timeframe: str,
    limit: int,
    cfg: SmartMoneyStrategyConfig,
    bt_cfg: BacktestConfig,
):
    print(f"\n=== SMART_MONEY en {symbol} {timeframe} (limit={limit}) ===")

    df = get_datos_cripto_cached(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        force_download=False,
    )
    print(f"Filas obtenidas: {len(df)}")

    strategy = SmartMoneyStrategy(config=cfg)
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
    # Valores óptimos obtenidos de opt_smart_money_BTCUSDT_15m.csv
    # fvg_min_size_pct=0.05, trend_ema_window=200, allow_short=True
    # sl_pct=0.02, tp_rr=2.0

    smc_cfg = SmartMoneyStrategyConfig(
        fvg_min_size_pct=0.05,
        trend_ema_window=200,
        allow_short=True,
        use_fvg=True,
        use_ob=False,
    )

    bt_cfg = BacktestConfig(
        initial_capital=1000.0,
        sl_pct=0.02,     # 2% SL
        tp_rr=2.0,       # TP 1:2
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
        row = run_smart_money_on_market(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            cfg=smc_cfg,
            bt_cfg=bt_cfg,
        )
        rows.append(row)

    print("\n===== RESUMEN VALIDACIÓN CRUZADA SMART_MONEY =====")
    df_summary = pd.DataFrame(rows)
    df_summary = df_summary.sort_values(
        by="total_return_pct", ascending=False
    ).reset_index(drop=True)
    print(df_summary)


if __name__ == "__main__":
    main()
