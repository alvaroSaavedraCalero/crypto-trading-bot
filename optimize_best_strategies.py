#!/usr/bin/env python3
"""
Focused optimization for best performing strategies: KELTNER and BOLLINGER_MR
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.table import Table

from optimization.generic_optimizer import GenericOptimizer
from data.downloader import get_datos_cripto_cached

console = Console()


def optimize_keltner():
    """Optimize KELTNER strategy for BTC/USDT."""
    console.print("\n[bold cyan]Optimizing KELTNER for BTC/USDT...[/bold cyan]")

    # Download data
    df = get_datos_cripto_cached("BTC/USDT", "15m", 10000, force_download=False)

    # Parameter ranges - focused on most impactful parameters
    param_ranges = {
        "kc_window": [20, 25, 30, 35, 40],
        "kc_mult": [2.0, 2.25, 2.5, 2.75, 3.0],
        "atr_window": [14, 20],
        "atr_min_percentile": [0.3, 0.4, 0.5],
        "use_trend_filter": [True, False],
        "trend_ema_window": [100],
        "allow_short": [True],
        "side_mode": ["both"],
    }

    backtest_params = {
        "sl_pct": [0.005, 0.0075, 0.01, 0.015],
        "tp_rr": [2.0, 2.5, 3.0],
    }

    # Create optimizer
    optimizer = GenericOptimizer(
        strategy_type="KELTNER",
        param_ranges=param_ranges,
        min_trades=25,
    )

    # Build grid
    param_grid = optimizer.build_param_grid(backtest_param_ranges=backtest_params)
    console.print(f"  Testing {len(param_grid)} parameter combinations...")

    # Optimize
    results = optimizer.optimize(
        df=df,
        backtest_param_ranges=backtest_params,
        metric="profit_factor",
        n_jobs=None,  # Use all available cores
    )

    if results.empty:
        console.print("  [red]✗ No valid results[/red]")
        return None

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"opt_keltner_btc_{timestamp}.csv"
    results.to_csv(output_file, index=False)

    # Show top 5
    console.print("\n[green]Top 5 KELTNER configurations:[/green]\n")
    top5 = results.head(5)

    for idx, row in top5.iterrows():
        console.print(
            f"{idx+1}. PF={row['profit_factor']:.2f}, "
            f"Return={row['total_return_pct']:.2f}%, "
            f"WR={row['winrate_pct']:.1f}%, "
            f"Trades={row['num_trades']}, "
            f"kc_window={row['kc_window']}, "
            f"kc_mult={row['kc_mult']:.2f}, "
            f"sl={row['sl_pct']:.3f}, "
            f"tp_rr={row['tp_rr']:.1f}"
        )

    console.print(f"\n[green]✓ Results saved to: {output_file}[/green]")
    return results


def optimize_bollinger_mr():
    """Optimize BOLLINGER_MR strategy across multiple pairs."""
    console.print("\n[bold cyan]Optimizing BOLLINGER_MR for multiple pairs...[/bold cyan]")

    all_results = []

    for symbol in ["BTC/USDT", "ETH/USDT", "BNB/USDT"]:
        console.print(f"\n  Optimizing for {symbol}...")

        df = get_datos_cripto_cached(symbol, "15m", 10000, force_download=False)

        # Parameter ranges
        param_ranges = {
            "bb_window": [15, 20, 25],
            "bb_std": [1.8, 2.0, 2.2, 2.5],
            "rsi_window": [10, 14, 21],
            "rsi_oversold": [15.0, 20.0, 25.0, 30.0],
            "rsi_overbought": [65.0, 70.0, 75.0, 80.0],
        }

        backtest_params = {
            "sl_pct": [0.01, 0.015, 0.02],
            "tp_rr": [1.5, 2.0, 2.5],
        }

        optimizer = GenericOptimizer(
            strategy_type="BOLLINGER_MR",
            param_ranges=param_ranges,
            min_trades=25,
        )

        param_grid = optimizer.build_param_grid(backtest_param_ranges=backtest_params)
        console.print(f"    Testing {len(param_grid)} combinations...")

        results = optimizer.optimize(
            df=df,
            backtest_param_ranges=backtest_params,
            metric="profit_factor",
            n_jobs=None,  # Use all available cores
        )

        if not results.empty:
            results["symbol"] = symbol
            all_results.append(results)

            # Show best for this pair
            best = results.iloc[0]
            console.print(
                f"    Best: PF={best['profit_factor']:.2f}, "
                f"Return={best['total_return_pct']:.2f}%, "
                f"WR={best['winrate_pct']:.1f}%"
            )

    if not all_results:
        console.print("  [red]✗ No valid results[/red]")
        return None

    # Combine and save
    all_results_df = pd.concat(all_results, ignore_index=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"opt_bollinger_mr_multi_{timestamp}.csv"
    all_results_df.to_csv(output_file, index=False)

    console.print(f"\n[green]✓ Results saved to: {output_file}[/green]")

    # Show best overall
    console.print("\n[green]Best configurations by pair:[/green]\n")
    for symbol in ["BTC/USDT", "ETH/USDT", "BNB/USDT"]:
        pair_results = all_results_df[all_results_df['symbol'] == symbol]
        if not pair_results.empty:
            best = pair_results.iloc[0]
            console.print(
                f"{symbol}: PF={best['profit_factor']:.2f}, "
                f"Return={best['total_return_pct']:.2f}%, "
                f"bb_window={best['bb_window']}, "
                f"bb_std={best['bb_std']:.1f}, "
                f"rsi_os={best['rsi_oversold']:.0f}"
            )

    return all_results_df


def main():
    console.print("\n[bold]🚀 Focused Strategy Optimization[/bold]")
    console.print("=" * 80)

    # Optimize KELTNER
    console.print("\n[bold]Phase 1: Optimize KELTNER (current best performer)[/bold]")
    keltner_results = optimize_keltner()

    # Optimize BOLLINGER_MR
    console.print("\n[bold]Phase 2: Optimize BOLLINGER_MR (near breakeven)[/bold]")
    bollinger_results = optimize_bollinger_mr()

    # Summary
    console.print("\n[bold cyan]Optimization Summary[/bold cyan]")
    console.print("=" * 80)

    if keltner_results is not None:
        best_keltner = keltner_results.iloc[0]
        console.print(
            f"\n✓ KELTNER Best: "
            f"PF={best_keltner['profit_factor']:.2f}, "
            f"Return={best_keltner['total_return_pct']:.2f}%, "
            f"Trades={best_keltner['num_trades']}"
        )

    if bollinger_results is not None:
        # Best overall across all pairs
        best_bollinger = bollinger_results.nlargest(1, 'profit_factor').iloc[0]
        console.print(
            f"✓ BOLLINGER_MR Best ({best_bollinger['symbol']}): "
            f"PF={best_bollinger['profit_factor']:.2f}, "
            f"Return={best_bollinger['total_return_pct']:.2f}%, "
            f"Trades={best_bollinger['num_trades']}"
        )

    console.print("\n[bold green]✅ Optimization complete![/bold green]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
