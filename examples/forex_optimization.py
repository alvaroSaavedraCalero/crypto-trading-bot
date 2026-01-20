#!/usr/bin/env python3
"""
Forex Strategy Optimization Example

This example demonstrates how to:
1. Optimize strategy parameters using grid search
2. Validate results with train/test split
3. Run walk-forward analysis for robustness testing

Works on any OS and in Europe without OANDA.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta

from src.core.types import Symbol, Timeframe, MarketType
from src.core.backtesting import BacktestConfig
from src.core.risk import RiskConfig
from src.core.optimization import (
    GridSearchOptimizer,
    OptimizationConfig,
    WalkForwardAnalyzer,
    WalkForwardConfig
)
from src.core.strategies.implementations.bollinger_mr import (
    BollingerMRStrategy,
    BollingerMRConfig
)
from src.adapters.data_sources import DataSourceFactory


def run_grid_search_optimization():
    """Run parameter optimization with train/validation split."""
    print("=" * 60)
    print("FOREX STRATEGY OPTIMIZATION")
    print("=" * 60)

    # 1. Setup
    symbol = Symbol("EUR", "USD", MarketType.FOREX)
    timeframe = Timeframe.from_string("15m")

    print(f"\nSymbol: {symbol}")
    print(f"Strategy: Bollinger Mean Reversion")

    # 2. Fetch data
    adapter = DataSourceFactory.create_forex()

    print("\nFetching data...")
    try:
        df = adapter.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=10000
        )
        print(f"Loaded {len(df)} candles")
    except Exception as e:
        print(f"Could not fetch data: {e}")
        return

    # 3. Split into train/validation (80/20)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()

    print(f"Training set: {len(train_df)} candles")
    print(f"Validation set: {len(val_df)} candles")

    # 4. Define parameter grid
    param_grid = {
        "bb_window": [15, 20, 25, 30],
        "bb_std": [1.5, 2.0, 2.5],
        "rsi_window": [7, 14, 21],
        "rsi_oversold": [20.0, 25.0, 30.0],
        "rsi_overbought": [70.0, 75.0, 80.0],
        "allow_short": [True],
    }

    total_combinations = 1
    for values in param_grid.values():
        total_combinations *= len(values)
    print(f"\nParameter combinations to test: {total_combinations}")

    # 5. Configure optimization
    opt_config = OptimizationConfig(
        n_jobs=-1,  # Use all CPU cores
        max_combinations=500,  # Limit for speed
        optimize_metric="profit_factor",
        min_trades=20
    )

    backtest_config = BacktestConfig(
        initial_capital=10000.0,
        sl_pct=0.015,
        tp_rr=2.0,
        fee_pct=0.0002,
        allow_short=True
    )

    risk_config = RiskConfig(risk_pct=0.01)

    # 6. Run optimization with validation
    print("\nRunning optimization...")
    optimizer = GridSearchOptimizer(opt_config, risk_config)

    results = optimizer.optimize_with_validation(
        train_df=train_df,
        validation_df=val_df,
        strategy_class=BollingerMRStrategy,
        backtest_config=backtest_config,
        param_grid=param_grid,
        show_progress=True
    )

    # 7. Display results
    print("\n" + "=" * 60)
    print("OPTIMIZATION RESULTS")
    print("=" * 60)

    print(f"\nBest Parameters:")
    for param, value in results["best_params"].items():
        print(f"  {param}: {value}")

    print(f"\nTraining Performance:")
    train_m = results["train_metrics"]
    print(f"  Profit Factor: {train_m.profit_factor:.2f}")
    print(f"  Total Return: {train_m.total_return_pct:.2f}%")
    print(f"  Win Rate: {train_m.win_rate:.1f}%")
    print(f"  Max Drawdown: {train_m.max_drawdown_pct:.2f}%")
    print(f"  Trades: {train_m.num_trades}")

    print(f"\nValidation Performance (Out-of-Sample):")
    val_m = results["validation_metrics"]
    print(f"  Profit Factor: {val_m.profit_factor:.2f}")
    print(f"  Total Return: {val_m.total_return_pct:.2f}%")
    print(f"  Win Rate: {val_m.win_rate:.1f}%")
    print(f"  Max Drawdown: {val_m.max_drawdown_pct:.2f}%")
    print(f"  Trades: {val_m.num_trades}")

    print(f"\nDegradation (Train -> Validation): {results['degradation_pct']:.1f}%")

    # Warn about overfitting
    if results["degradation_pct"] > 50:
        print("\n⚠️  WARNING: High degradation suggests overfitting!")
        print("   Consider using walk-forward analysis.")
    elif results["degradation_pct"] > 25:
        print("\n⚠️  CAUTION: Moderate degradation detected.")
    else:
        print("\n✓ Results appear robust.")

    return results


def run_walk_forward_analysis():
    """Run walk-forward analysis for robust validation."""
    print("\n" + "=" * 60)
    print("WALK-FORWARD ANALYSIS")
    print("=" * 60)

    # Setup
    symbol = Symbol("GBP", "USD", MarketType.FOREX)
    timeframe = Timeframe.from_string("1h")

    adapter = DataSourceFactory.create_forex()

    print(f"\nSymbol: {symbol}")
    print("Fetching data...")

    try:
        df = adapter.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=8000  # More data for walk-forward
        )
        print(f"Loaded {len(df)} candles")
    except Exception as e:
        print(f"Could not fetch data: {e}")
        return

    # Parameter grid (smaller for walk-forward)
    param_grid = {
        "bb_window": [15, 20, 25],
        "bb_std": [2.0, 2.5],
        "rsi_window": [14],
        "rsi_oversold": [25.0, 30.0],
        "rsi_overbought": [70.0, 75.0],
        "allow_short": [True],
    }

    # Configure walk-forward
    wf_config = WalkForwardConfig(
        n_splits=5,        # 5 walk-forward windows
        train_pct=0.8,     # 80% train, 20% validation per window
        anchored=False,    # Rolling windows
        min_train_bars=500,
        min_validation_bars=100
    )

    opt_config = OptimizationConfig(
        n_jobs=-1,
        max_combinations=100,  # Faster for each window
        optimize_metric="profit_factor",
        min_trades=10
    )

    backtest_config = BacktestConfig(
        initial_capital=10000.0,
        sl_pct=0.02,
        tp_rr=2.0,
        fee_pct=0.0003,
        allow_short=True
    )

    # Run analysis
    print("\nRunning walk-forward analysis...")
    analyzer = WalkForwardAnalyzer(wf_config, opt_config)

    try:
        result = analyzer.analyze(
            df=df,
            strategy_class=BollingerMRStrategy,
            backtest_config=backtest_config,
            param_grid=param_grid,
            show_progress=True
        )

        # Display results
        print("\n" + result.summary())

        # Parameter stability interpretation
        print("\nParameter Stability Interpretation:")
        for param, cv in result.parameter_stability.items():
            if cv < 20:
                stability = "Stable ✓"
            elif cv < 50:
                stability = "Moderate"
            else:
                stability = "Unstable ⚠️"
            print(f"  {param}: CV={cv:.1f}% ({stability})")

        return result

    except Exception as e:
        print(f"Walk-forward analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("# PART 1: GRID SEARCH OPTIMIZATION")
    print("#" * 60)
    run_grid_search_optimization()

    print("\n" + "#" * 60)
    print("# PART 2: WALK-FORWARD ANALYSIS")
    print("#" * 60)
    run_walk_forward_analysis()
