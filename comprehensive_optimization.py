#!/usr/bin/env python3
"""
Comprehensive Strategy Optimization and Validation
Optimizes all strategies across multiple trading pairs and generates detailed reports.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import json

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from optimization.generic_optimizer import GenericOptimizer
from backtesting.engine import Backtester, BacktestConfig
from data.downloader import get_datos_cripto_cached
from config.settings import RISK_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


# ========== CONFIGURATION ==========
TRADING_PAIRS = [
    ("BTC/USDT", "15m", 10000),
    ("ETH/USDT", "15m", 10000),
    ("BNB/USDT", "15m", 10000),
    ("SOL/USDT", "15m", 10000),
]

# Strategy optimization configurations
STRATEGY_CONFIGS = {
    "MA_RSI": {
        "param_ranges": {
            "fast_window": [5, 10, 15, 20],
            "slow_window": [20, 30, 40, 50],
            "rsi_window": [10, 14, 21],
            "rsi_overbought": [65.0, 70.0, 75.0],
            "rsi_oversold": [25.0, 30.0, 35.0],
            "use_rsi_filter": [True, False],
            "signal_mode": ["cross"],
        },
        "backtest_params": {
            "sl_pct": [0.005, 0.01, 0.015, 0.02],
            "tp_rr": [1.5, 2.0, 2.5, 3.0],
        },
    },
    "SUPERTREND": {
        "param_ranges": {
            "atr_period": [10, 14, 20],
            "atr_multiplier": [2.0, 2.5, 3.0, 3.5],
            "use_adx_filter": [True, False],
            "adx_threshold": [20.0, 25.0],
        },
        "backtest_params": {
            "sl_pct": [0.01, 0.015, 0.02, 0.025],
            "tp_rr": [2.0, 2.5, 3.0, 4.0],
        },
    },
    "BOLLINGER_MR": {
        "param_ranges": {
            "bb_window": [15, 20, 25],
            "bb_std": [1.5, 2.0, 2.5],
            "rsi_window": [10, 14, 21],
            "rsi_oversold": [20.0, 25.0, 30.0],
            "rsi_overbought": [65.0, 70.0, 75.0],
        },
        "backtest_params": {
            "sl_pct": [0.01, 0.015, 0.02],
            "tp_rr": [1.5, 2.0, 2.5],
        },
    },
    "KELTNER": {
        "param_ranges": {
            "kc_window": [20, 30, 40],
            "kc_mult": [2.0, 2.5, 3.0],
            "atr_window": [14, 20],
            "atr_min_percentile": [0.3, 0.4, 0.5],
            "use_trend_filter": [True, False],
        },
        "backtest_params": {
            "sl_pct": [0.0075, 0.01, 0.015],
            "tp_rr": [2.0, 2.5, 3.0],
        },
    },
}


def optimize_strategy_for_pair(
    strategy_type: str,
    config: Dict[str, Any],
    symbol: str,
    timeframe: str,
    limit: int,
) -> Dict[str, Any]:
    """Optimize a single strategy for a specific trading pair."""
    console.print(f"\n[cyan]Optimizing {strategy_type} for {symbol} {timeframe}...[/cyan]")

    try:
        # Download data
        df = get_datos_cripto_cached(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            force_download=False,
        )

        # Create optimizer
        optimizer = GenericOptimizer(
            strategy_type=strategy_type,
            param_ranges=config["param_ranges"],
            min_trades=20,
        )

        # Build parameter grid
        param_grid = optimizer.build_param_grid(
            backtest_param_ranges=config["backtest_params"]
        )

        console.print(f"  Testing {len(param_grid)} parameter combinations...")

        # Run optimization
        results = optimizer.optimize(
            df=df,
            metric="profit_factor",
            parallel=True,
            n_jobs=-1,
        )

        if results.empty:
            console.print(f"  [red]✗ No valid results for {strategy_type} on {symbol}[/red]")
            return None

        # Get best result
        best = results.iloc[0].to_dict()
        best["symbol"] = symbol
        best["timeframe"] = timeframe
        best["strategy"] = strategy_type

        console.print(
            f"  [green]✓ Best result: "
            f"Return={best['total_return_pct']:.2f}%, "
            f"Winrate={best['winrate_pct']:.2f}%, "
            f"Trades={best['num_trades']}[/green]"
        )

        return best

    except Exception as e:
        console.print(f"  [red]✗ Error optimizing {strategy_type} on {symbol}: {e}[/red]")
        logger.error(f"Optimization failed: {e}", exc_info=True)
        return None


def validate_strategy(
    strategy_type: str,
    best_params: Dict[str, Any],
    validation_pairs: List[tuple],
) -> List[Dict[str, Any]]:
    """Validate optimized strategy on different pairs."""
    console.print(f"\n[yellow]Validating {strategy_type} on {len(validation_pairs)} pairs...[/yellow]")

    from strategies.registry import STRATEGY_REGISTRY

    strategy_cls, config_cls = STRATEGY_REGISTRY[strategy_type]

    # Extract strategy parameters
    config_fields = {f.name for f in config_cls.__dataclass_fields__.values()}
    strategy_params = {k: v for k, v in best_params.items() if k in config_fields}

    # Extract backtest parameters
    bt_config = BacktestConfig(
        initial_capital=1000.0,
        sl_pct=best_params.get("sl_pct", 0.02),
        tp_rr=best_params.get("tp_rr", 2.0),
        fee_pct=0.0005,
        allow_short=True,
    )

    results = []
    for symbol, timeframe, limit in validation_pairs:
        try:
            df = get_datos_cripto_cached(symbol, timeframe, limit, force_download=False)

            # Create strategy
            strategy_config = config_cls(**strategy_params)
            strategy = strategy_cls(config=strategy_config)

            # Generate signals
            df_signals = strategy.generate_signals(df)

            # Run backtest
            bt = Backtester(backtest_config=bt_config, risk_config=RISK_CONFIG)
            result = bt.run(df_signals)

            results.append({
                "strategy": strategy_type,
                "symbol": symbol,
                "timeframe": timeframe,
                "num_trades": result.num_trades,
                "total_return_pct": result.total_return_pct,
                "max_drawdown_pct": result.max_drawdown_pct,
                "winrate_pct": result.winrate_pct,
                "profit_factor": result.profit_factor,
            })

            console.print(
                f"  {symbol}: Return={result.total_return_pct:.2f}%, "
                f"Winrate={result.winrate_pct:.2f}%"
            )

        except Exception as e:
            console.print(f"  [red]✗ Error on {symbol}: {e}[/red]")

    return results


def generate_html_report(
    optimization_results: pd.DataFrame,
    validation_results: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generate comprehensive HTML report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Strategy Optimization Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; background-color: white; }}
            th {{ background-color: #3498db; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .metric {{ font-weight: bold; }}
            .positive {{ color: #27ae60; }}
            .negative {{ color: #e74c3c; }}
            .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>📊 Comprehensive Strategy Optimization Report</h1>
        <p>Generated: {timestamp}</p>

        <div class="summary">
            <h2>Summary Statistics</h2>
            <p><strong>Strategies Tested:</strong> {len(optimization_results['strategy'].unique())}</p>
            <p><strong>Trading Pairs:</strong> {len(optimization_results['symbol'].unique())}</p>
            <p><strong>Total Configurations:</strong> {len(optimization_results)}</p>
        </div>

        <h2>Best Performing Configurations by Strategy</h2>
        {optimization_results.to_html(index=False, classes='table', float_format=lambda x: f'{x:.2f}')}

        <h2>Validation Results</h2>
        {validation_results.to_html(index=False, classes='table', float_format=lambda x: f'{x:.2f}')}

        <h2>Strategy Performance Comparison</h2>
        {validation_results.groupby('strategy').agg({
            'total_return_pct': 'mean',
            'winrate_pct': 'mean',
            'profit_factor': 'mean',
            'max_drawdown_pct': 'mean',
            'num_trades': 'sum'
        }).round(2).to_html(classes='table')}
    </body>
    </html>
    """

    output_path.write_text(html)
    console.print(f"\n[green]✓ HTML report generated: {output_path}[/green]")


def main():
    console.print("\n[bold]🚀 Comprehensive Strategy Optimization[/bold]\n")
    console.print("=" * 80)

    all_optimization_results = []
    all_validation_results = []

    # Phase 1: Optimize each strategy for each pair
    console.print("\n[bold cyan]Phase 1: Strategy Optimization[/bold cyan]")

    for strategy_type, config in STRATEGY_CONFIGS.items():
        console.print(f"\n[bold]Strategy: {strategy_type}[/bold]")

        for symbol, timeframe, limit in TRADING_PAIRS:
            result = optimize_strategy_for_pair(
                strategy_type=strategy_type,
                config=config,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )

            if result:
                all_optimization_results.append(result)

    # Save optimization results
    if not all_optimization_results:
        console.print("\n[red]✗ No optimization results generated[/red]")
        return 1

    df_optimization = pd.DataFrame(all_optimization_results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = Path(f"optimization_results_{timestamp}.csv")
    df_optimization.to_csv(csv_path, index=False)
    console.print(f"\n[green]✓ Optimization results saved: {csv_path}[/green]")

    # Phase 2: Validate best strategies across all pairs
    console.print("\n[bold cyan]Phase 2: Cross-Pair Validation[/bold cyan]")

    for strategy_type in STRATEGY_CONFIGS.keys():
        # Get best result for this strategy (across all pairs during optimization)
        strategy_results = df_optimization[df_optimization['strategy'] == strategy_type]

        if strategy_results.empty:
            continue

        best_result = strategy_results.nlargest(1, 'profit_factor').iloc[0].to_dict()

        # Validate on all pairs
        validation_results = validate_strategy(
            strategy_type=strategy_type,
            best_params=best_result,
            validation_pairs=TRADING_PAIRS,
        )

        all_validation_results.extend(validation_results)

    # Save validation results
    if all_validation_results:
        df_validation = pd.DataFrame(all_validation_results)
        validation_csv = Path(f"validation_results_{timestamp}.csv")
        df_validation.to_csv(validation_csv, index=False)
        console.print(f"\n[green]✓ Validation results saved: {validation_csv}[/green]")

        # Generate HTML report
        html_path = Path(f"optimization_report_{timestamp}.html")
        generate_html_report(df_optimization, df_validation, html_path)

    # Phase 3: Display summary
    console.print("\n[bold cyan]Phase 3: Final Summary[/bold cyan]")

    summary_table = Table(title="Strategy Performance Summary")
    summary_table.add_column("Strategy", style="cyan")
    summary_table.add_column("Avg Return %", style="green")
    summary_table.add_column("Avg Winrate %", style="yellow")
    summary_table.add_column("Avg Profit Factor", style="magenta")
    summary_table.add_column("Total Trades", style="blue")

    if all_validation_results:
        summary = df_validation.groupby('strategy').agg({
            'total_return_pct': 'mean',
            'winrate_pct': 'mean',
            'profit_factor': 'mean',
            'num_trades': 'sum',
        }).round(2)

        for strategy, row in summary.iterrows():
            summary_table.add_row(
                strategy,
                f"{row['total_return_pct']:.2f}",
                f"{row['winrate_pct']:.2f}",
                f"{row['profit_factor']:.2f}",
                str(int(row['num_trades'])),
            )

        console.print("\n")
        console.print(summary_table)

        # Find best overall strategy
        best_strategy = summary['total_return_pct'].idxmax()
        console.print(f"\n[bold green]🏆 Best Overall Strategy: {best_strategy}[/bold green]")
        console.print(f"   Average Return: {summary.loc[best_strategy, 'total_return_pct']:.2f}%")
        console.print(f"   Average Winrate: {summary.loc[best_strategy, 'winrate_pct']:.2f}%")

    console.print("\n[bold green]✅ Optimization complete![/bold green]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
