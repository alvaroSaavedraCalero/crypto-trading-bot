#!/usr/bin/env python3
"""
Forex Strategy Parameter Optimization

Optimizes all strategies on EURUSD and USDJPY pairs.
Uses grid search with different parameter combinations.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
from itertools import product
import json

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from strategies.registry import STRATEGY_REGISTRY
from backtesting.engine import Backtester, BacktestConfig
from utils.risk import RiskManagementConfig
from utils.logger import get_logger
from data.yfinance_downloader import get_yfinance_data

logger = get_logger(__name__)
console = Console()

# Forex pairs to optimize
PAIRS = ["EURUSD", "USDJPY"]
TIMEFRAME = "15m"
LIMIT = 2500

# Parameter grids for each strategy (simplified for faster optimization)
PARAM_GRIDS = {
    "SUPERTREND": {
        "atr_period": [10, 14],
        "atr_multiplier": [2.5, 3.0],
        "use_adx_filter": [False],
        "adx_threshold": [20.0],
    },
    "BOLLINGER_MR": {
        "bb_window": [15, 20, 25],
        "bb_std": [2.0, 2.5],
        "rsi_window": [14],
        "rsi_oversold": [25.0, 30.0],
        "rsi_overbought": [70.0, 75.0],
    },
    "MA_RSI": {
        "fast_window": [10, 12],
        "slow_window": [20, 30],
        "rsi_window": [14],
        "rsi_overbought": [70.0],
        "rsi_oversold": [30.0],
        "use_rsi_filter": [False],
    },
    "KELTNER": {
        "kc_window": [25, 30],
        "kc_mult": [2.0, 2.5],
        "atr_window": [20],
        "atr_min_percentile": [0.4],
    },
}

# Backtest config
BACKTEST_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    sl_pct=0.02,
    tp_rr=2.0,
    fee_pct=0.0005,
    allow_short=True,
)

RISK_CONFIG = RiskManagementConfig(risk_pct=0.01)


def count_combinations(param_grid: Dict[str, List]) -> int:
    """Count total parameter combinations"""
    count = 1
    for values in param_grid.values():
        count *= len(values)
    return count


def get_param_combinations(param_grid: Dict[str, List]) -> List[Dict[str, Any]]:
    """Generate all parameter combinations from grid"""
    keys = param_grid.keys()
    values = param_grid.values()
    combinations = []
    
    for combo in product(*values):
        param_dict = dict(zip(keys, combo))
        combinations.append(param_dict)
    
    return combinations


def test_strategy_params(
    strategy_name: str,
    pair: str,
    df: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Test a strategy with specific parameters"""
    
    try:
        if df is None or df.empty:
            return {
                "strategy": strategy_name,
                "pair": pair,
                "params": params,
                "status": "failed",
                "return": 0.0,
                "winrate": 0.0,
                "trades": 0,
                "pf": 0.0,
                "dd": 0.0,
            }
        
        # Get strategy class and config class
        if strategy_name not in STRATEGY_REGISTRY:
            return {
                "strategy": strategy_name,
                "pair": pair,
                "params": params,
                "status": "not_found",
                "return": 0.0,
                "winrate": 0.0,
                "trades": 0,
                "pf": 0.0,
                "dd": 0.0,
            }
        
        strategy_class, config_class = STRATEGY_REGISTRY[strategy_name]
        
        # Create strategy instance with parameters
        try:
            config = config_class(**params)
            strategy = strategy_class(config)
        except Exception as e:
            logger.debug(f"Could not create {strategy_name} with params {params}: {e}")
            return {
                "strategy": strategy_name,
                "pair": pair,
                "params": params,
                "status": "instantiation_error",
                "return": 0.0,
                "winrate": 0.0,
                "trades": 0,
                "pf": 0.0,
                "dd": 0.0,
            }
        
        # Generate signals
        try:
            df_signals = strategy.generate_signals(df.copy())
        except Exception as e:
            logger.debug(f"Error generating signals: {e}")
            return {
                "strategy": strategy_name,
                "pair": pair,
                "params": params,
                "status": "signal_error",
                "return": 0.0,
                "winrate": 0.0,
                "trades": 0,
                "pf": 0.0,
                "dd": 0.0,
            }
        
        # Run backtest
        backtester = Backtester(BACKTEST_CONFIG, RISK_CONFIG)
        results = backtester.run(df_signals)
        
        if not results or not results.trades:
            return {
                "strategy": strategy_name,
                "pair": pair,
                "params": params,
                "status": "no_trades",
                "return": 0.0,
                "winrate": 0.0,
                "trades": 0,
                "pf": 0.0,
                "dd": 0.0,
            }
        
        # Extract metrics
        return {
            "strategy": strategy_name,
            "pair": pair,
            "params": params,
            "status": "success",
            "return": round(results.total_return_pct, 2),
            "winrate": round(results.winrate_pct, 1),
            "trades": results.num_trades,
            "pf": round(results.profit_factor, 2),
            "dd": round(results.max_drawdown_pct, 2),
        }
        
    except Exception as e:
        logger.error(f"Error testing {strategy_name} on {pair}: {e}")
        return {
            "strategy": strategy_name,
            "pair": pair,
            "params": params,
            "status": "error",
            "return": 0.0,
            "winrate": 0.0,
            "trades": 0,
            "pf": 0.0,
            "dd": 0.0,
        }


def optimize_strategy(
    strategy_name: str,
    data_dict: Dict[str, pd.DataFrame],
    progress: Progress,
    task_id,
) -> List[Dict[str, Any]]:
    """Optimize a single strategy across all pairs"""
    
    if strategy_name not in PARAM_GRIDS:
        console.print(f"[yellow]⚠️  No parameter grid defined for {strategy_name}[/yellow]")
        return []
    
    param_grid = PARAM_GRIDS[strategy_name]
    combinations = get_param_combinations(param_grid)
    total_combos = len(combinations) * len(PAIRS)
    
    results = []
    
    for params in combinations:
        for pair in PAIRS:
            if pair in data_dict:
                result = test_strategy_params(
                    strategy_name,
                    pair,
                    data_dict[pair],
                    params
                )
                results.append(result)
            
            progress.update(task_id, advance=1)
    
    return results


def main():
    """Main optimization function"""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]    FOREX STRATEGY PARAMETER OPTIMIZATION                    [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    # Fetch data
    console.print(f"[bold]Fetching Forex Data ({TIMEFRAME})...[/bold]\n")
    
    data_dict = {}
    for pair in PAIRS:
        try:
            df = get_yfinance_data(
                symbol=pair,
                timeframe=TIMEFRAME,
                limit=LIMIT,
                period="60d"
            )
            
            if df is not None and not df.empty:
                console.print(f"[green]✓ {pair}: Loaded {len(df)} candles[/green]")
                data_dict[pair] = df
            else:
                console.print(f"[red]✗ {pair}: No data returned[/red]")
        except Exception as e:
            console.print(f"[red]✗ {pair}: {str(e)[:80]}[/red]")
    
    if not data_dict:
        console.print("[red bold]✗ Failed to download any forex data![/red bold]")
        return
    
    # Count total combinations
    strategies_to_optimize = [s for s in PARAM_GRIDS.keys() if s in STRATEGY_REGISTRY]
    total_tests = sum(
        count_combinations(PARAM_GRIDS[s]) * len(PAIRS) 
        for s in strategies_to_optimize
    )
    
    console.print(f"\n[bold]Optimizing {len(strategies_to_optimize)} strategies...[/bold]")
    console.print(f"[cyan]Total parameter combinations to test: {total_tests:,}[/cyan]\n")
    
    # Run optimization with progress bar
    all_results = []
    
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Optimizing...", total=total_tests)
        
        for strategy_name in strategies_to_optimize:
            console.print(f"[bold magenta]→ {strategy_name}[/bold magenta]")
            results = optimize_strategy(strategy_name, data_dict, progress, task)
            all_results.extend(results)
    
    if not all_results:
        console.print("[red]No results to display[/red]")
        return
    
    # Convert to DataFrame
    results_df = pd.DataFrame(all_results)
    
    # Filter successful results
    successful = results_df[results_df["status"] == "success"]
    
    if successful.empty:
        console.print("[yellow]⚠️  No successful backtest results[/yellow]")
    else:
        console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]           TOP 10 BEST PARAMETER COMBINATIONS                  [/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
        
        # Sort by return
        top_results = successful.nlargest(10, "return")
        
        table = Table(title="Best Configurations")
        table.add_column("Rank", style="cyan")
        table.add_column("Strategy", style="magenta")
        table.add_column("Pair")
        table.add_column("Return %", justify="right", style="green")
        table.add_column("Winrate %", justify="right")
        table.add_column("Trades", justify="right")
        table.add_column("PF", justify="right")
        
        for idx, (_, row) in enumerate(top_results.iterrows(), 1):
            return_style = "green" if row["return"] > 0 else "red"
            table.add_row(
                str(idx),
                row["strategy"],
                row["pair"],
                f"[{return_style}]{row['return']:.2f}[/{return_style}]",
                f"{row['winrate']:.1f}",
                str(row['trades']),
                f"{row['pf']:.2f}"
            )
        
        console.print(table)
        
        # Best per strategy
        console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]              BEST PARAMETERS PER STRATEGY                     [/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
        
        best_by_strategy = successful.loc[successful.groupby("strategy")["return"].idxmax()]
        
        best_params_summary = {}
        
        for _, row in best_by_strategy.iterrows():
            strategy = row["strategy"]
            pair = row["pair"]
            return_pct = row["return"]
            params = row["params"]
            
            best_params_summary[strategy] = {
                "best_pair": pair,
                "return": return_pct,
                "trades": row["trades"],
                "winrate": row["winrate"],
                "pf": row["pf"],
                "parameters": params
            }
            
            table = Table(title=f"{strategy} - Best Config")
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="green")
            
            for param_name, param_value in params.items():
                table.add_row(param_name, str(param_value))
            
            table.add_row("", "")
            table.add_row("Return %", f"{return_pct:.2f}")
            table.add_row("Winrate %", f"{row['winrate']:.1f}")
            table.add_row("Trades", str(row['trades']))
            table.add_row("Profit Factor", f"{row['pf']:.2f}")
            table.add_row("Pair", pair)
            
            console.print(table)
            console.print()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all results
        results_file = f"forex_optimization_results_{timestamp}.csv"
        results_df.to_csv(results_file, index=False)
        
        # Save best params as JSON
        params_file = f"forex_best_params_{timestamp}.json"
        with open(params_file, "w") as f:
            json.dump(best_params_summary, f, indent=2)
        
        console.print(f"[green]✓ Results saved to: {results_file}[/green]")
        console.print(f"[green]✓ Best params saved to: {params_file}[/green]\n")
        
        # Statistics
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]                    OPTIMIZATION STATISTICS                   [/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
        
        stats_table = Table()
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Tests", str(len(all_results)))
        stats_table.add_row("Successful", str(len(successful)))
        stats_table.add_row("Success Rate", f"{len(successful)/len(all_results)*100:.1f}%")
        stats_table.add_row("Best Return", f"{successful['return'].max():.2f}%")
        stats_table.add_row("Avg Return", f"{successful['return'].mean():.2f}%")
        stats_table.add_row("Avg Winrate", f"{successful['winrate'].mean():.1f}%")
        stats_table.add_row("Avg Trades", f"{successful['trades'].mean():.0f}")
        
        console.print(stats_table)
        console.print()


if __name__ == "__main__":
    main()
