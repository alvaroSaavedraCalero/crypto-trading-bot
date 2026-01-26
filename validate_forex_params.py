#!/usr/bin/env python3
"""
Validate and Report Optimized Forex Strategy Parameters
"""

import sys
from pathlib import Path
from datetime import datetime
import json

import pandas as pd
from rich.console import Console
from rich.table import Table

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

# Configuration
PAIRS = ["EURUSD", "USDJPY"]
TIMEFRAME = "15m"
LIMIT = 2500

BACKTEST_CONFIG = BacktestConfig(
    initial_capital=10000.0,
    sl_pct=0.02,
    tp_rr=2.0,
    fee_pct=0.0005,
    allow_short=True,
)

RISK_CONFIG = RiskManagementConfig(risk_pct=0.01)


def validate_optimized_params():
    """Validate and test the optimized parameters"""
    
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]    OPTIMIZED PARAMETERS VALIDATION - FOREX STRATEGIES      [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    # Load best params
    params_file = "forex_best_params_20260126_154943.json"
    
    if not Path(params_file).exists():
        console.print(f"[red]✗ File not found: {params_file}[/red]")
        return
    
    with open(params_file, "r") as f:
        best_params = json.load(f)
    
    # Fetch data
    console.print(f"[bold]Fetching Forex Data...[/bold]\n")
    
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
                console.print(f"[green]✓ {pair}: {len(df)} candles[/green]")
                data_dict[pair] = df
        except Exception as e:
            console.print(f"[red]✗ {pair}: {str(e)[:60]}[/red]")
    
    if not data_dict:
        console.print("[red]Failed to fetch data[/red]")
        return
    
    # Validate each strategy
    console.print(f"\n[bold]Validating Optimized Strategies...[/bold]\n")
    
    validation_results = []
    
    for strategy_name, best_config in best_params.items():
        console.print(f"[bold magenta]→ {strategy_name}[/bold magenta]")
        
        params = best_config["parameters"]
        
        # Test on each pair
        for pair in PAIRS:
            if pair not in data_dict:
                continue
            
            try:
                strategy_class, config_class = STRATEGY_REGISTRY[strategy_name]
                
                # Create strategy
                config = config_class(**params)
                strategy = strategy_class(config)
                
                # Generate signals
                df_signals = strategy.generate_signals(data_dict[pair].copy())
                
                # Run backtest
                backtester = Backtester(BACKTEST_CONFIG, RISK_CONFIG)
                results = backtester.run(df_signals)
                
                validation_results.append({
                    "strategy": strategy_name,
                    "pair": pair,
                    "return": round(results.total_return_pct, 2),
                    "winrate": round(results.winrate_pct, 1),
                    "trades": results.num_trades,
                    "pf": round(results.profit_factor, 2),
                    "dd": round(results.max_drawdown_pct, 2),
                    "status": "✓",
                })
                
                console.print(f"  {pair}: Return={results.total_return_pct:.2f}%, Trades={results.num_trades}")
                
            except Exception as e:
                console.print(f"  {pair}: Error - {str(e)[:50]}")
                validation_results.append({
                    "strategy": strategy_name,
                    "pair": pair,
                    "return": 0.0,
                    "winrate": 0.0,
                    "trades": 0,
                    "pf": 0.0,
                    "dd": 0.0,
                    "status": "✗",
                })
    
    # Display results
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]              VALIDATION RESULTS - ALL PAIRS                  [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    results_df = pd.DataFrame(validation_results)
    
    # By pair
    for pair in PAIRS:
        pair_results = results_df[results_df["pair"] == pair]
        
        if pair_results.empty:
            continue
        
        console.print(f"[bold]{pair}[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Strategy", style="cyan")
        table.add_column("Return %", justify="right")
        table.add_column("Winrate %", justify="right")
        table.add_column("Trades", justify="right")
        table.add_column("PF", justify="right")
        table.add_column("Max DD %", justify="right")
        table.add_column("Status", justify="center")
        
        for _, row in pair_results.iterrows():
            return_color = "green" if row["return"] > 0 else "red"
            table.add_row(
                row["strategy"],
                f"[{return_color}]{row['return']:.2f}[/{return_color}]",
                f"{row['winrate']:.1f}",
                str(row['trades']),
                f"{row['pf']:.2f}",
                f"{row['dd']:.2f}",
                row['status']
            )
        
        console.print(table)
        console.print()
    
    # Summary
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]                   SUMMARY STATISTICS                        [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    summary_table = Table()
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    successful = results_df[results_df["status"] == "✓"]
    
    if not successful.empty:
        summary_table.add_row("Total Tests", str(len(results_df)))
        summary_table.add_row("Successful", str(len(successful)))
        summary_table.add_row("Success Rate", f"{len(successful)/len(results_df)*100:.1f}%")
        summary_table.add_row("Best Return", f"{successful['return'].max():.2f}%")
        summary_table.add_row("Avg Return", f"{successful['return'].mean():.2f}%")
        summary_table.add_row("Total Trades", str(int(successful['trades'].sum())))
        summary_table.add_row("Avg Winrate", f"{successful['winrate'].mean():.1f}%")
    else:
        summary_table.add_row("Status", "No successful tests")
    
    console.print(summary_table)
    
    # Save validation results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"forex_validation_report_{timestamp}.csv"
    results_df.to_csv(output_file, index=False)
    
    console.print(f"\n[green]✓ Validation report saved to: {output_file}[/green]\n")
    
    # Show summary of best params by strategy
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]           RECOMMENDED PARAMETERS FOR PRODUCTION            [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    for strategy_name, config in best_params.items():
        console.print(f"[bold magenta]{strategy_name}[/bold magenta]")
        
        params = config["parameters"]
        params_table = Table()
        params_table.add_column("Parameter", style="cyan")
        params_table.add_column("Value", style="green")
        
        for param, value in params.items():
            params_table.add_row(param, str(value))
        
        console.print(params_table)
        console.print()


if __name__ == "__main__":
    validate_optimized_params()
