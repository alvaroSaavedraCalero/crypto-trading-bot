#!/usr/bin/env python3
"""
Forex Strategy Test - Using Yahoo Finance data
Tests multiple forex pairs with different strategies
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
from rich.console import Console
from rich.table import Table

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from strategies.registry import STRATEGY_REGISTRY
from backtesting.engine import Backtester, BacktestConfig
from utils.risk import RiskManagementConfig
from config.settings import RISK_CONFIG
from utils.logger import get_logger
from data.yfinance_downloader import get_yfinance_data

logger = get_logger(__name__)
console = Console()

# Forex pairs to test
FOREX_PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
]

TIMEFRAME = "15m"
LIMIT = 2000  # Number of candles


def get_forex_data(pair: str) -> pd.DataFrame:
    """Fetch forex data from Yahoo Finance"""
    try:
        df = get_yfinance_data(
            symbol=pair,
            timeframe=TIMEFRAME,
            limit=LIMIT,
            period="60d"
        )
        
        if df is None or df.empty:
            console.print(f"[red]✗ {pair}: No data returned[/red]")
            return None
            
        console.print(f"[green]✓ {pair}: Loaded {len(df)} candles[/green]")
        return df
        
    except Exception as e:
        console.print(f"[red]✗ {pair}: {str(e)[:80]}[/red]")
        return None


def test_strategy_on_pair(
    strategy_name: str,
    pair: str,
    df: pd.DataFrame,
    config_overrides: Dict = None
) -> Dict:
    """Test a strategy on a forex pair"""
    
    if df is None or df.empty:
        return {
            "pair": pair,
            "strategy": strategy_name,
            "status": "failed",
            "return": 0,
            "winrate": 0,
            "trades": 0,
            "pf": 0,
            "dd": 0,
        }
    
    try:
        # Get strategy class and config class
        if strategy_name not in STRATEGY_REGISTRY:
            return {
                "pair": pair,
                "strategy": strategy_name,
                "status": "not_found",
                "return": 0,
                "winrate": 0,
                "trades": 0,
                "pf": 0,
                "dd": 0,
            }
        
        strategy_info = STRATEGY_REGISTRY[strategy_name]
        strategy_class = strategy_info[0]
        config_class = strategy_info[1]
        
        # Create strategy instance with default config
        try:
            config = config_class()
            strategy = strategy_class(config)
        except Exception:
            # Try without config
            try:
                strategy = strategy_class()
            except Exception as e:
                logger.error(f"Could not instantiate {strategy_name}: {e}")
                return {
                    "pair": pair,
                    "strategy": strategy_name,
                    "status": "instantiation_error",
                    "return": 0,
                    "winrate": 0,
                    "trades": 0,
                    "pf": 0,
                    "dd": 0,
                }
        
        # Setup backtest config
        backtest_config = BacktestConfig(
            initial_capital=10000.0,
            sl_pct=0.02,
            tp_rr=2.0,
            fee_pct=0.0005,
            allow_short=True,
        )
        
        # Setup risk config
        risk_config = RiskManagementConfig(risk_pct=0.01)
        
        # Generate signals
        try:
            df_signals = strategy.generate_signals(df.copy())
        except Exception as e:
            logger.error(f"Error generating signals for {strategy_name} on {pair}: {e}")
            return {
                "pair": pair,
                "strategy": strategy_name,
                "status": "signal_error",
                "return": 0,
                "winrate": 0,
                "trades": 0,
                "pf": 0,
                "dd": 0,
            }
        
        # Run backtest
        backtester = Backtester(backtest_config, risk_config)
        results = backtester.run(df_signals)
        
        if not results or not results.trades:
            return {
                "pair": pair,
                "strategy": strategy_name,
                "status": "no_trades",
                "return": 0,
                "winrate": 0,
                "trades": 0,
                "pf": 0,
                "dd": 0,
            }
        
        # Extract metrics from BacktestResult
        return {
            "pair": pair,
            "strategy": strategy_name,
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
            "pair": pair,
            "strategy": strategy_name,
            "status": "error",
            "return": 0,
            "winrate": 0,
            "trades": 0,
            "pf": 0,
            "dd": 0,
        }


def main():
    """Main test function"""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]       FOREX STRATEGY TEST - Yahoo Finance Data       [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")
    
    # Strategies to test
    strategies_to_test = ["SUPERTREND", "BOLLINGER_MR", "MA_RSI", "KELTNER"]
    
    console.print(f"[bold]Fetching Forex Data ({TIMEFRAME})...[/bold]\n")
    
    # Download all data first
    data_dict = {}
    for pair in FOREX_PAIRS:
        df = get_forex_data(pair)
        if df is not None and not df.empty:
            data_dict[pair] = df
    
    if not data_dict:
        console.print("[red bold]✗ Failed to download any forex data![/red bold]")
        return
    
    console.print(f"\n[bold]Testing Strategies ({len(strategies_to_test)})...[/bold]\n")
    
    # Test each strategy on each pair
    all_results = []
    
    for strategy_name in strategies_to_test:
        console.print(f"[bold magenta]Testing {strategy_name}...[/bold magenta]")
        
        for pair in FOREX_PAIRS:
            if pair in data_dict:
                result = test_strategy_on_pair(strategy_name, pair, data_dict[pair])
                all_results.append(result)
                
                if result["status"] == "success":
                    console.print(f"  {pair}: [green]Return={result['return']}%, WR={result['winrate']}%, Trades={result['trades']}[/green]")
                else:
                    console.print(f"  {pair}: [yellow]Status={result['status']}[/yellow]")
    
    if not all_results:
        console.print("[red]No results to display[/red]")
        return
    
    # Convert to DataFrame for analysis
    results_df = pd.DataFrame(all_results)
    
    # Display results by strategy
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]              RESULTS BY STRATEGY                       [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")
    
    # Summary table
    summary = results_df[results_df["status"] == "success"].groupby("strategy").agg({
        "return": "mean",
        "winrate": "mean",
        "trades": "sum",
        "pf": "mean",
        "dd": "mean"
    }).round(2)
    
    if not summary.empty:
        summary = summary.sort_values("return", ascending=False)
        
        table = Table(title="Strategy Performance Summary")
        table.add_column("Strategy", style="cyan")
        table.add_column("Avg Return %", justify="right", style="green")
        table.add_column("Avg Winrate %", justify="right")
        table.add_column("Avg PF", justify="right")
        table.add_column("Total Trades", justify="right")
        table.add_column("Avg DD %", justify="right", style="red")
        
        for strategy, row in summary.iterrows():
            table.add_row(
                strategy,
                f"{row['return']:.2f}",
                f"{row['winrate']:.1f}",
                f"{row['pf']:.2f}",
                f"{int(row['trades'])}",
                f"{row['dd']:.2f}"
            )
        
        console.print(table)
    
    # Detailed results by pair
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]              DETAILED RESULTS BY PAIR                 [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")
    
    for pair in FOREX_PAIRS:
        pair_results = results_df[(results_df["pair"] == pair) & (results_df["status"] == "success")]
        
        if not pair_results.empty:
            console.print(f"[bold]{pair}[/bold]")
            
            table = Table(show_header=True, header_style="bold")
            table.add_column("Strategy", style="cyan")
            table.add_column("Return %", justify="right")
            table.add_column("Winrate %", justify="right")
            table.add_column("Trades", justify="right")
            table.add_column("Profit Factor", justify="right")
            
            for _, row in pair_results.iterrows():
                return_style = "green" if row["return"] > 0 else "red"
                table.add_row(
                    row["strategy"],
                    f"[{return_style}]{row['return']:.2f}[/{return_style}]",
                    f"{row['winrate']:.1f}",
                    str(row['trades']),
                    f"{row['pf']:.2f}"
                )
            
            console.print(table)
            console.print()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"forex_test_results_{timestamp}.csv"
    results_df.to_csv(output_file, index=False)
    console.print(f"[green]✓ Results saved to: {output_file}[/green]\n")


if __name__ == "__main__":
    main()
