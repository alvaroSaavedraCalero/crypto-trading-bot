# src/core/optimization/walk_forward.py
"""
Walk-Forward Analysis for robust strategy validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .grid_search import GridSearchOptimizer
from .optimizer import OptimizationConfig
from ..backtesting import BacktestConfig, Backtester
from ..risk import RiskConfig
from ..types import BacktestMetrics, BacktestResult


@dataclass
class WalkForwardConfig:
    """
    Configuration for Walk-Forward Analysis.

    Walk-forward analysis splits data into multiple in-sample (training)
    and out-of-sample (validation) periods to test strategy robustness.
    """
    # Number of walk-forward windows
    n_splits: int = 5

    # Ratio of in-sample to out-of-sample period
    # 0.8 means 80% training, 20% validation
    train_pct: float = 0.8

    # Whether to use anchored (expanding) or rolling windows
    anchored: bool = False

    # Minimum number of bars for training
    min_train_bars: int = 500

    # Minimum number of bars for validation
    min_validation_bars: int = 100

    def __post_init__(self) -> None:
        if self.n_splits < 2:
            raise ValueError("n_splits must be at least 2")

        if not 0.5 <= self.train_pct <= 0.95:
            raise ValueError("train_pct must be between 0.5 and 0.95")


@dataclass
class WalkForwardWindow:
    """Single walk-forward window results."""
    window_number: int
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    best_params: Dict[str, Any]
    train_metrics: BacktestMetrics
    validation_metrics: BacktestMetrics
    degradation_pct: float


@dataclass
class WalkForwardResult:
    """
    Complete Walk-Forward Analysis results.
    """
    windows: List[WalkForwardWindow] = field(default_factory=list)
    combined_equity_curve: Optional[pd.Series] = None
    combined_metrics: Optional[BacktestMetrics] = None

    # Summary statistics
    avg_train_return: float = 0.0
    avg_validation_return: float = 0.0
    avg_degradation: float = 0.0
    consistency_score: float = 0.0  # % of profitable validation periods

    # Parameter stability
    parameter_stability: Dict[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        """Return human-readable summary."""
        lines = [
            "=" * 50,
            "WALK-FORWARD ANALYSIS RESULTS",
            "=" * 50,
            f"Windows analyzed: {len(self.windows)}",
            f"Avg training return: {self.avg_train_return:.2f}%",
            f"Avg validation return: {self.avg_validation_return:.2f}%",
            f"Avg degradation: {self.avg_degradation:.2f}%",
            f"Consistency score: {self.consistency_score:.1f}%",
            "",
            "Combined out-of-sample metrics:",
        ]

        if self.combined_metrics:
            lines.extend([
                f"  Total return: {self.combined_metrics.total_return_pct:.2f}%",
                f"  Max drawdown: {self.combined_metrics.max_drawdown_pct:.2f}%",
                f"  Profit factor: {self.combined_metrics.profit_factor:.2f}",
                f"  Win rate: {self.combined_metrics.win_rate:.1f}%",
                f"  Sharpe ratio: {self.combined_metrics.sharpe_ratio:.2f}",
            ])

        if self.parameter_stability:
            lines.extend(["", "Parameter stability (coefficient of variation):"])
            for param, cv in self.parameter_stability.items():
                lines.append(f"  {param}: {cv:.2f}")

        return "\n".join(lines)


class WalkForwardAnalyzer:
    """
    Walk-Forward Analysis engine.

    Performs rolling or anchored optimization and validation to assess
    strategy robustness and detect overfitting.
    """

    def __init__(
        self,
        wf_config: WalkForwardConfig,
        opt_config: OptimizationConfig,
        risk_config: Optional[RiskConfig] = None
    ) -> None:
        self.wf_config = wf_config
        self.opt_config = opt_config
        self.risk_config = risk_config or RiskConfig()

    def analyze(
        self,
        df: pd.DataFrame,
        strategy_class: type,
        backtest_config: BacktestConfig,
        param_grid: Dict[str, List[Any]],
        show_progress: bool = True
    ) -> WalkForwardResult:
        """
        Run Walk-Forward Analysis.

        Args:
            df: Full OHLCV DataFrame
            strategy_class: Strategy class to optimize
            backtest_config: Backtest configuration
            param_grid: Parameter grid for optimization
            show_progress: Show progress bar

        Returns:
            WalkForwardResult with all window results and combined metrics
        """
        # Sort by timestamp
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Generate windows
        windows = self._generate_windows(df)

        if show_progress:
            print(f"Running Walk-Forward Analysis with {len(windows)} windows...")

        results: List[WalkForwardWindow] = []
        all_validation_trades = []
        all_validation_equity = []

        optimizer = GridSearchOptimizer(self.opt_config, self.risk_config)

        for i, (train_idx, val_idx) in enumerate(windows):
            train_df = df.iloc[train_idx].copy()
            val_df = df.iloc[val_idx].copy()

            if show_progress:
                print(f"\nWindow {i + 1}/{len(windows)}")
                print(f"  Training: {train_df['timestamp'].iloc[0]} to {train_df['timestamp'].iloc[-1]}")
                print(f"  Validation: {val_df['timestamp'].iloc[0]} to {val_df['timestamp'].iloc[-1]}")

            # Optimize on training data
            try:
                opt_result = optimizer.optimize_with_validation(
                    train_df=train_df,
                    validation_df=val_df,
                    strategy_class=strategy_class,
                    backtest_config=backtest_config,
                    param_grid=param_grid,
                    show_progress=False
                )

                window_result = WalkForwardWindow(
                    window_number=i + 1,
                    train_start=train_df["timestamp"].iloc[0],
                    train_end=train_df["timestamp"].iloc[-1],
                    validation_start=val_df["timestamp"].iloc[0],
                    validation_end=val_df["timestamp"].iloc[-1],
                    best_params=opt_result["best_params"],
                    train_metrics=opt_result["train_metrics"],
                    validation_metrics=opt_result["validation_metrics"],
                    degradation_pct=opt_result["degradation_pct"],
                )

                results.append(window_result)

                # Collect validation results for combined metrics
                # Re-run validation backtest to get trades
                config_class = strategy_class.__annotations__.get("config", type(opt_result["best_params"]))
                strategy = strategy_class(config_class(**opt_result["best_params"]))
                val_signals = strategy.generate_signals(val_df.copy())

                backtester = Backtester(backtest_config, self.risk_config)
                val_backtest = backtester.run(val_signals)

                all_validation_trades.extend(val_backtest.trades)
                if val_backtest.equity_curve is not None:
                    all_validation_equity.append(val_backtest.equity_curve)

                if show_progress:
                    print(f"  Train PF: {window_result.train_metrics.profit_factor:.2f}")
                    print(f"  Val PF: {window_result.validation_metrics.profit_factor:.2f}")
                    print(f"  Degradation: {window_result.degradation_pct:.1f}%")

            except Exception as e:
                if show_progress:
                    print(f"  Window failed: {e}")
                continue

        if not results:
            raise ValueError("All walk-forward windows failed")

        # Calculate summary statistics
        return self._build_result(
            results,
            all_validation_equity,
            backtest_config.initial_capital
        )

    def _generate_windows(
        self,
        df: pd.DataFrame
    ) -> List[tuple[range, range]]:
        """Generate train/validation index windows."""
        n_rows = len(df)
        n_splits = self.wf_config.n_splits

        # Calculate window sizes
        total_val_pct = 1 - self.wf_config.train_pct
        val_size = max(
            self.wf_config.min_validation_bars,
            int(n_rows * total_val_pct / n_splits)
        )

        windows = []

        if self.wf_config.anchored:
            # Anchored (expanding) walk-forward
            # Training window expands, validation window rolls
            for i in range(n_splits):
                val_end = n_rows - (n_splits - i - 1) * val_size
                val_start = val_end - val_size

                if val_start < self.wf_config.min_train_bars:
                    continue

                train_start = 0
                train_end = val_start

                if train_end - train_start < self.wf_config.min_train_bars:
                    continue

                windows.append((
                    range(train_start, train_end),
                    range(val_start, val_end)
                ))
        else:
            # Rolling walk-forward
            # Both training and validation windows roll
            train_size = int(
                (n_rows - val_size * n_splits) / n_splits * self.wf_config.train_pct
            ) + int(n_rows * self.wf_config.train_pct / n_splits)

            train_size = max(train_size, self.wf_config.min_train_bars)

            step = (n_rows - train_size - val_size) // max(1, n_splits - 1)

            for i in range(n_splits):
                train_start = i * step
                train_end = train_start + train_size

                if train_end + val_size > n_rows:
                    break

                val_start = train_end
                val_end = val_start + val_size

                windows.append((
                    range(train_start, train_end),
                    range(val_start, val_end)
                ))

        return windows

    def _build_result(
        self,
        windows: List[WalkForwardWindow],
        validation_equity: List[pd.Series],
        initial_capital: float
    ) -> WalkForwardResult:
        """Build final WalkForwardResult."""
        # Average metrics
        avg_train_return = np.mean([w.train_metrics.total_return_pct for w in windows])
        avg_val_return = np.mean([w.validation_metrics.total_return_pct for w in windows])
        avg_degradation = np.mean([w.degradation_pct for w in windows])

        # Consistency score (% profitable validation periods)
        profitable_windows = sum(
            1 for w in windows
            if w.validation_metrics.total_return_pct > 0
        )
        consistency_score = (profitable_windows / len(windows)) * 100

        # Parameter stability (coefficient of variation)
        param_stability = {}
        all_params = [w.best_params for w in windows]

        for param in all_params[0].keys():
            values = [p[param] for p in all_params]
            if all(isinstance(v, (int, float)) for v in values):
                mean_val = np.mean(values)
                std_val = np.std(values)
                cv = (std_val / mean_val * 100) if mean_val != 0 else 0
                param_stability[param] = cv

        # Combined equity curve (sequential)
        combined_equity = None
        if validation_equity:
            # Chain equity curves, adjusting for ending capital
            combined = []
            current_capital = initial_capital

            for eq in validation_equity:
                if len(eq) == 0:
                    continue

                # Scale to current capital level
                start_val = eq.iloc[0]
                if start_val > 0:
                    scaled = eq * (current_capital / start_val)
                    combined.append(scaled)
                    current_capital = scaled.iloc[-1]

            if combined:
                combined_equity = pd.concat(combined)

        # Combined metrics from validation periods
        combined_metrics = None
        if windows:
            # Use average of validation metrics
            combined_metrics = BacktestMetrics(
                total_return_pct=avg_val_return,
                profit_factor=np.mean([w.validation_metrics.profit_factor for w in windows]),
                win_rate=np.mean([w.validation_metrics.win_rate for w in windows]),
                max_drawdown_pct=np.mean([w.validation_metrics.max_drawdown_pct for w in windows]),
                sharpe_ratio=np.mean([w.validation_metrics.sharpe_ratio for w in windows]),
                num_trades=sum(w.validation_metrics.num_trades for w in windows),
            )

        return WalkForwardResult(
            windows=windows,
            combined_equity_curve=combined_equity,
            combined_metrics=combined_metrics,
            avg_train_return=avg_train_return,
            avg_validation_return=avg_val_return,
            avg_degradation=avg_degradation,
            consistency_score=consistency_score,
            parameter_stability=param_stability,
        )
