#!/usr/bin/env python3
"""
Quick Strategy Test - Evaluate all strategies with current parameters
"""

import sys
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd
from rich.console import Console
from rich.table import Table

from strategies.registry import STRATEGY_REGISTRY
from backtesting.engine import Backtester, BacktestConfig
from data.downloader import get_datos_cripto_cached
from config.settings import RISK_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


TEST_PAIRS = [
    ("BTC/USDT", "15m", 5000),
    ("ETH/USDT", "15m", 5000),
    ("BNB/USDT", "15m", 5000),
]

# Default configs for quick testing
DEFAULT_CONFIGS = {
    "MA_RSI": {
        "fast_window": 10,
        "slow_window": 30,
        "rsi_window": 14,
        "rsi_overbought": 70.0,
        "rsi_oversold": 30.0,
        "use_rsi_filter": False,
        "signal_mode": "cross",
    },
    "SUPERTREND": {
        "atr_period": 14,
        "atr_multiplier": 3.0,
        "use_adx_filter": False,
        "adx_threshold": 20.0,
    },
    "BOLLINGER_MR": {
        "bb_window": 20,
        "bb_std": 2.0,
        "rsi_window": 14,
        "rsi_oversold": 25.0,
        "rsi_overbought": 70.0,
    },
    "KELTNER": {
        "kc_window": 30,
        "kc_mult": 2.5,
        "atr_window": 20,
        "atr_min_percentile": 0.4,
        "use_trend_filter": False,
    },
}


def test_strategy(
    strategy_type: str,
    config_params: Dict[str, Any],
    symbol: str,
    timeframe: str,
    limit: int,
) -> Dict[str, Any]:
    """Test a single strategy configuration."""
    try:
        # Get strategy classes
        strategy_cls, config_cls = STRATEGY_REGISTRY[strategy_type]

        # Download data
        df = get_datos_cripto_cached(symbol, timeframe, limit, force_download=False)

        # Create strategy
        strategy_config = config_cls(**config_params)
        strategy = strategy_cls(config=strategy_config)

        # Generate signals
        df_signals = strategy.generate_signals(df)

        # Backtest config
        bt_config = BacktestConfig(
            initial_capital=1000.0,
            sl_pct=0.015,
            tp_rr=2.0,
            fee_pct=0.0005,
            allow_short=True,
        )

        # Run backtest
        bt = Backtester(backtest_config=bt_config, risk_config=RISK_CONFIG)
        result = bt.run(df_signals)

        return {
            "strategy": strategy_type,
            "symbol": symbol,
            "timeframe": timeframe,
            "num_trades": result.num_trades,
            "total_return_pct": result.total_return_pct,
            "max_drawdown_pct": result.max_drawdown_pct,
            "winrate_pct": result.winrate_pct,
            "profit_factor": result.profit_factor,
            "status": "✓",
        }

    except Exception as e:
        logger.error(f"Error testing {strategy_type} on {symbol}: {e}")
        return {
            "strategy": strategy_type,
            "symbol": symbol,
            "timeframe": timeframe,
            "num_trades": 0,
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "winrate_pct": 0.0,
            "profit_factor": 0.0,
            "status": f"✗ {str(e)[:30]}",
        }


def main():
    console.print("\n[bold]📊 Quick Strategy Evaluation[/bold]\n")
    console.print("Testing strategies with default parameters across multiple pairs...")
    console.print("=" * 80)

    results = []

    for strategy_type, config_params in DEFAULT_CONFIGS.items():
        console.print(f"\n[cyan]Testing {strategy_type}...[/cyan]")

        for symbol, timeframe, limit in TEST_PAIRS:
            result = test_strategy(
                strategy_type=strategy_type,
                config_params=config_params,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
            results.append(result)

            console.print(
                f"  {symbol}: {result['status']} "
                f"Return={result['total_return_pct']:.2f}%, "
                f"Winrate={result['winrate_pct']:.2f}%, "
                f"Trades={result['num_trades']}"
            )

    # Create results DataFrame
    df_results = pd.DataFrame(results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"quick_test_results_{timestamp}.csv"
    df_results.to_csv(output_file, index=False)

    # Display summary table
    console.print("\n[bold]Strategy Performance Summary[/bold]\n")

    summary_table = Table(title="Average Performance by Strategy")
    summary_table.add_column("Strategy", style="cyan")
    summary_table.add_column("Avg Return %", justify="right", style="green")
    summary_table.add_column("Avg Winrate %", justify="right", style="yellow")
    summary_table.add_column("Avg PF", justify="right", style="magenta")
    summary_table.add_column("Total Trades", justify="right", style="blue")
    summary_table.add_column("Avg DD %", justify="right", style="red")

    summary = df_results.groupby('strategy').agg({
        'total_return_pct': 'mean',
        'winrate_pct': 'mean',
        'profit_factor': 'mean',
        'num_trades': 'sum',
        'max_drawdown_pct': 'mean',
    }).round(2)

    for strategy, row in summary.iterrows():
        summary_table.add_row(
            strategy,
            f"{row['total_return_pct']:.2f}",
            f"{row['winrate_pct']:.2f}",
            f"{row['profit_factor']:.2f}",
            str(int(row['num_trades'])),
            f"{abs(row['max_drawdown_pct']):.2f}",
        )

    console.print(summary_table)

    # Best and worst performers
    best_strategy = summary['total_return_pct'].idxmax()
    worst_strategy = summary['total_return_pct'].idxmin()

    console.print(f"\n[bold green]🏆 Best Strategy: {best_strategy}[/bold green]")
    console.print(f"   Average Return: {summary.loc[best_strategy, 'total_return_pct']:.2f}%")

    console.print(f"\n[bold red]⚠️  Worst Strategy: {worst_strategy}[/bold red]")
    console.print(f"   Average Return: {summary.loc[worst_strategy, 'total_return_pct']:.2f}%")

    # Recommendations
    console.print("\n[bold]📝 Recommendations:[/bold]")

    for strategy, row in summary.iterrows():
        if row['total_return_pct'] < 0:
            console.print(f"  • {strategy}: [red]Needs optimization - negative returns[/red]")
        elif row['profit_factor'] < 1.0:
            console.print(f"  • {strategy}: [yellow]Needs optimization - PF < 1.0[/yellow]")
        elif row['winrate_pct'] < 40:
            console.print(f"  • {strategy}: [yellow]Low winrate - consider parameter tuning[/yellow]")
        else:
            console.print(f"  • {strategy}: [green]Performing well - ready for optimization[/green]")

    console.print(f"\n[green]✓ Results saved to: {output_file}[/green]\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
