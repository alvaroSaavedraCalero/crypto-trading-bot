#!/usr/bin/env python3
"""
Unified Optimizer-Validator Pipeline
Runs optimization, extracts best configs, validates across markets, and generates reports.
"""

import subprocess
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

from backtesting.engine import BacktestConfig, Backtester
from config.settings import RISK_CONFIG
from data.downloader import get_datos_cripto_cached

# ========== CONFIGURATION ==========
VALIDATION_MARKETS = [
    ("BTC/USDT", "1m", 10000),
    ("ETH/USDT", "1m", 10000),
    ("SOL/USDT", "1m", 10000),
    ("BNB/USDT", "1m", 10000),
    ("XRP/USDT", "1m", 10000),
]

# Strategy mapping: optimizer_name -> (strategy_class, config_class, csv_pattern)
STRATEGY_MAP = {
    "bollinger": {
        "optimizer": "optimization.optimize_bollinger",
        "csv_pattern": "opt_bollinger_*.csv",
        "strategy_module": "strategies.bollinger_mean_reversion",
        "strategy_class": "BollingerMeanReversionStrategy",
        "config_class": "BollingerMeanReversionStrategyConfig",
        "config_params": ["bb_window", "bb_std", "rsi_window", "rsi_oversold", "rsi_overbought"],
        "bt_params": ["sl_pct", "tp_rr"],
    },
    "ict": {
        "optimizer": "optimization.optimize_ict",
        "csv_pattern": "opt_ict_*.csv",
        "strategy_module": "strategies.ict_strategy",
        "strategy_class": "ICTStrategy",
        "config_class": "ICTStrategyConfig",
        "config_params": ["kill_zone", "fvg_min_pips"],
        "bt_params": ["sl_pct", "tp_rr"],
    },
    "macd_adx": {
        "optimizer": "optimization.optimize_macd_adx",
        "csv_pattern": "opt_macd_adx_*.csv",
        "strategy_module": "strategies.macd_adx_trend_strategy",
        "strategy_class": "MACDADXTrendStrategy",
        "config_class": "MACDADXTrendStrategyConfig",
        "config_params": ["fast_ema", "slow_ema", "signal_ema", "trend_ema_window", "adx_window", "adx_threshold", "allow_short"],
        "bt_params": ["sl_pct", "tp_rr"],
    },
    # Add more strategies as needed
}
# ===================================


def run_optimizer(module_name: str) -> bool:
    """Run a single optimizer module."""
    print(f"\n{'='*80}")
    print(f"Running Optimizer: {module_name}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", module_name],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✓ {module_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {module_name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n✗ {module_name} failed with error: {e}")
        return False


def find_latest_csv(pattern: str) -> Path | None:
    """Find the most recent CSV file matching the pattern."""
    files = list(Path(".").glob(pattern))
    if not files:
        return None
    # Return the most recently modified file
    return max(files, key=lambda p: p.stat().st_mtime)


def extract_best_config(csv_path: Path) -> dict:
    """Extract the best configuration (first row) from optimizer CSV."""
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV file {csv_path} is empty")
    
    # First row is the best (optimizers sort by total_return_pct descending)
    best_row = df.iloc[0].to_dict()
    return best_row


def validate_on_market(strategy_class, config, bt_config, symbol: str, timeframe: str, limit: int) -> dict:
    """Run validation on a single market."""
    print(f"  Testing on {symbol} {timeframe}...")
    
    df = get_datos_cripto_cached(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        force_download=False,
    )
    
    strategy = strategy_class(config=config)
    df_signals = strategy.generate_signals(df)
    
    bt = Backtester(
        backtest_config=bt_config,
        risk_config=RISK_CONFIG,
    )
    result = bt.run(df_signals)
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "num_trades": result.num_trades,
        "total_return_pct": result.total_return_pct,
        "max_drawdown_pct": result.max_drawdown_pct,
        "winrate_pct": result.winrate_pct,
        "profit_factor": result.profit_factor,
    }


def run_validation_for_strategy(strategy_name: str, strategy_info: dict) -> list[dict]:
    """Run validation for a single strategy across all markets."""
    print(f"\n{'='*80}")
    print(f"Validating: {strategy_name}")
    print(f"{'='*80}\n")
    
    # Find CSV
    csv_path = find_latest_csv(strategy_info["csv_pattern"])
    if not csv_path:
        print(f"⚠ No CSV found for {strategy_name}, skipping validation")
        return []
    
    print(f"Reading best config from: {csv_path}")
    best_config_dict = extract_best_config(csv_path)
    
    # Import strategy classes dynamically
    module = __import__(strategy_info["strategy_module"], fromlist=[strategy_info["strategy_class"], strategy_info["config_class"]])
    strategy_class = getattr(module, strategy_info["strategy_class"])
    config_class = getattr(module, strategy_info["config_class"])
    
    # Build config from CSV
    config_params = {k: best_config_dict[k] for k in strategy_info["config_params"] if k in best_config_dict}
    strategy_config = config_class(**config_params)
    
    # Build backtest config
    bt_config = BacktestConfig(
        initial_capital=1000.0,
        sl_pct=best_config_dict.get("sl_pct", 0.02),
        tp_rr=best_config_dict.get("tp_rr", 2.0),
        fee_pct=0.0005,
        allow_short=best_config_dict.get("allow_short", True),
    )
    
    # Run validation on all markets
    results = []
    for symbol, timeframe, limit in VALIDATION_MARKETS:
        try:
            result = validate_on_market(strategy_class, strategy_config, bt_config, symbol, timeframe, limit)
            result["strategy"] = strategy_name
            results.append(result)
        except Exception as e:
            print(f"  ✗ Error on {symbol}: {e}")
    
    return results


def main():
    print("="*80)
    print("OPTIMIZER-VALIDATOR PIPELINE")
    print("="*80)
    
    # Step 1: Run all optimizers
    print("\n[STEP 1] Running Optimizers...")
    for strategy_name, strategy_info in STRATEGY_MAP.items():
        run_optimizer(strategy_info["optimizer"])
    
    # Step 2: Run validation for each strategy
    print("\n[STEP 2] Running Validation...")
    all_results = []
    
    for strategy_name, strategy_info in STRATEGY_MAP.items():
        results = run_validation_for_strategy(strategy_name, strategy_info)
        all_results.extend(results)
    
    # Step 3: Generate report
    if not all_results:
        print("\n⚠ No validation results to report")
        return
    
    print("\n[STEP 3] Generating Report...")
    df_results = pd.DataFrame(all_results)
    
    # Save full results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"validation_summary_{timestamp}.csv"
    df_results.to_csv(output_path, index=False)
    print(f"\n✓ Full results saved to: {output_path}")
    
    # Print summary by strategy
    print("\n" + "="*80)
    print("VALIDATION SUMMARY BY STRATEGY")
    print("="*80)
    
    summary = df_results.groupby("strategy").agg({
        "total_return_pct": "mean",
        "winrate_pct": "mean",
        "max_drawdown_pct": "mean",
        "profit_factor": "mean",
        "num_trades": "sum",
    }).round(2)
    
    print(summary)
    
    # Print best performing strategy
    best_strategy = summary["total_return_pct"].idxmax()
    print(f"\n🏆 Best Overall Strategy: {best_strategy}")
    print(f"   Average Return: {summary.loc[best_strategy, 'total_return_pct']:.2f}%")


if __name__ == "__main__":
    main()
