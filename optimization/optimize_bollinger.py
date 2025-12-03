
from dataclasses import replace
from itertools import product
from typing import Iterable
import pandas as pd

from config.settings import BACKTEST_CONFIG, RISK_CONFIG
from data.downloader import get_datos_cripto_cached
from backtesting.engine import Backtester
from strategies.bollinger_mean_reversion import (
    BollingerMeanReversionStrategy,
    BollingerMeanReversionStrategyConfig,
)
from optimization.base_optimizer import run_optimization, get_global_df, save_results


def _evaluate_config(args: tuple) -> dict | None:
    df = get_global_df()

    (
        bb_window,
        bb_std,
        rsi_window,
        rsi_oversold,
        rsi_overbought,
        sl_pct,
        tp_rr,
        min_trades,
    ) = args

    strat_cfg = BollingerMeanReversionStrategyConfig(
        bb_window=bb_window,
        bb_std=bb_std,
        rsi_window=rsi_window,
        rsi_oversold=rsi_oversold,
        rsi_overbought=rsi_overbought,
    )

    strategy = BollingerMeanReversionStrategy(config=strat_cfg)

    bt_cfg = replace(
        BACKTEST_CONFIG,
        sl_pct=sl_pct,
        tp_rr=tp_rr,
        atr_mult_sl=None,
        atr_mult_tp=None,
        allow_short=True,
    )

    df_signals = strategy.generate_signals(df)

    backtester = Backtester(
        backtest_config=bt_cfg,
        risk_config=RISK_CONFIG,
    )
    result = backtester.run(df_signals)

    if result.num_trades < min_trades:
        return None

    return {
        "bb_window": bb_window,
        "bb_std": bb_std,
        "rsi_window": rsi_window,
        "rsi_oversold": rsi_oversold,
        "rsi_overbought": rsi_overbought,
        "sl_pct": sl_pct,
        "tp_rr": tp_rr,
        "num_trades": result.num_trades,
        "total_return_pct": result.total_return_pct,
        "max_drawdown_pct": result.max_drawdown_pct,
        "winrate_pct": result.winrate_pct,
        "profit_factor": result.profit_factor,
    }


def _build_param_grid(
    bb_windows: Iterable[int],
    bb_stds: Iterable[float],
    rsi_windows: Iterable[int],
    rsi_oversolds: Iterable[float],
    rsi_overboughts: Iterable[float],
    sl_pcts: Iterable[float],
    tp_rrs: Iterable[float],
    min_trades: int,
) -> list[tuple]:
    combos: list[tuple] = []

    for (
        bb_window,
        bb_std,
        rsi_window,
        rsi_oversold,
        rsi_overbought,
        sl_pct,
        tp_rr,
    ) in product(
        bb_windows,
        bb_stds,
        rsi_windows,
        rsi_oversolds,
        rsi_overboughts,
        sl_pcts,
        tp_rrs,
    ):
        combos.append(
            (
                bb_window,
                bb_std,
                rsi_window,
                rsi_oversold,
                rsi_overbought,
                sl_pct,
                tp_rr,
                min_trades,
            )
        )

    return combos


def main():
    # ========== CONFIGURATION ==========
    SYMBOL = "BNB/USDT"
    TIMEFRAME = "1m"
    LIMIT = 10000
    MIN_TRADES = 30
    # ===================================

    print(f"Optimizing Bollinger Mean Reversion for {SYMBOL} {TIMEFRAME}...")
    print(f"Obteniendo datos de {SYMBOL} en timeframe {TIMEFRAME}...")
    df = get_datos_cripto_cached(
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        limit=LIMIT,
        force_download=False,
    )
    print(f"Filas obtenidas: {len(df)}")

    # ==============================
    # Espacio de parámetros
    # ==============================
    bb_windows = [20, 30, 40]
    bb_stds = [2.0, 2.5]
    
    rsi_windows = [14]
    rsi_oversolds = [25.0, 30.0, 35.0]
    rsi_overboughts = [65.0, 70.0, 75.0]

    sl_pcts = [0.01, 0.015, 0.02] 
    tp_rrs = [1.0, 1.5, 2.0] 

    param_grid = _build_param_grid(
        bb_windows=bb_windows,
        bb_stds=bb_stds,
        rsi_windows=rsi_windows,
        rsi_oversolds=rsi_oversolds,
        rsi_overboughts=rsi_overboughts,
        sl_pcts=sl_pcts,
        tp_rrs=tp_rrs,
        min_trades=MIN_TRADES,
    )

    results = run_optimization(
        evaluator_func=_evaluate_config,
        param_grid=param_grid,
        df=df,
        max_combos=2000,
    )

    save_results(
        results=results,
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        strategy_name="Bollinger",
    )


if __name__ == "__main__":
    main()
