
from dataclasses import replace
from itertools import product
from typing import Iterable
import pandas as pd

from config.settings import BACKTEST_CONFIG, RISK_CONFIG
from data.downloader import get_datos_cripto_cached
from backtesting.engine import Backtester
from strategies.ict_strategy import (
    ICTStrategy,
    ICTStrategyConfig,
)
from optimization.base_optimizer import run_optimization, get_global_df, save_results


def _evaluate_config(args: tuple) -> dict | None:
    df = get_global_df()

    (
        kill_zone_start,
        kill_zone_end,
        swing_length,
        fvg_min_size_pct,
        allow_short,
        sl_pct,
        tp_rr,
        min_trades,
    ) = args

    strat_cfg = ICTStrategyConfig(
        kill_zone_start_hour=kill_zone_start,
        kill_zone_end_hour=kill_zone_end,
        swing_length=swing_length,
        fvg_min_size_pct=fvg_min_size_pct,
        allow_short=allow_short,
    )

    strategy = ICTStrategy(config=strat_cfg)

    bt_cfg = replace(
        BACKTEST_CONFIG,
        sl_pct=sl_pct,
        tp_rr=tp_rr,
        atr_mult_sl=None,
        atr_mult_tp=None,
        allow_short=allow_short,
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
        "kill_zone_start": kill_zone_start,
        "kill_zone_end": kill_zone_end,
        "swing_length": swing_length,
        "fvg_min_size_pct": fvg_min_size_pct,
        "allow_short": allow_short,
        "sl_pct": sl_pct,
        "tp_rr": tp_rr,
        "num_trades": result.num_trades,
        "total_return_pct": result.total_return_pct,
        "max_drawdown_pct": result.max_drawdown_pct,
        "winrate_pct": result.winrate_pct,
        "profit_factor": result.profit_factor,
    }


def _build_param_grid(
    kill_zones: Iterable[tuple[int, int]],
    swing_lengths: Iterable[int],
    fvg_min_sizes: Iterable[float],
    allow_shorts: Iterable[bool],
    sl_pcts: Iterable[float],
    tp_rrs: Iterable[float],
    min_trades: int,
) -> list[tuple]:
    combos: list[tuple] = []

    for (
        (kz_start, kz_end),
        swing_len,
        fvg_min,
        allow_short,
        sl_pct,
        tp_rr,
    ) in product(
        kill_zones,
        swing_lengths,
        fvg_min_sizes,
        allow_shorts,
        sl_pcts,
        tp_rrs,
    ):
        combos.append(
            (
                kz_start,
                kz_end,
                swing_len,
                fvg_min,
                allow_short,
                sl_pct,
                tp_rr,
                min_trades,
            )
        )

    return combos


def main():
    # ========== CONFIGURATION ==========
    SYMBOL = "BTC/USDT"
    TIMEFRAME = "1m"
    LIMIT = 10000
    MIN_TRADES = 30
    # ===================================

    print(f"Optimizing ICT Strategy for {SYMBOL} {TIMEFRAME}...")
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
    
    # Kill Zones (UTC)
    kill_zones = [
        (7, 10),   # London
        (12, 15),  # NY
        (0, 23),   # All day (control)
    ]
    
    swing_lengths = [5, 10]
    fvg_min_sizes = [0.05, 0.1, 0.2]
    
    allow_shorts = [True, False]
    sl_pcts = [0.01, 0.015, 0.02]
    tp_rrs = [2.0, 3.0, 4.0] # ICT busca R:R alto

    # ==============================
    # Configuración de la optimización
    # ==============================
    MIN_TRADES_OPT = 5  # Mínimo de trades para considerar una configuración válida
    MAX_COMBOS_OPT = 2000 # Máximo de combinaciones a probar (para limitar el tiempo)

    param_grid = _build_param_grid(
        kill_zones=kill_zones,
        swing_lengths=swing_lengths,
        fvg_min_sizes=fvg_min_sizes,
        allow_shorts=allow_shorts,
        sl_pcts=sl_pcts,
        tp_rrs=tp_rrs,
        min_trades=MIN_TRADES,
    )

    results = run_optimization(
        evaluator_func=_evaluate_config,
        param_grid=param_grid,
        df=df,
        max_combos=MAX_COMBOS_OPT,
    )

    save_results(
        results=results,
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        strategy_name="ICT",
    )


if __name__ == "__main__":
    main()
