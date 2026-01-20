# src/core/optimization/grid_search.py
"""
Grid search optimizer with parallel processing.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import pickle

import pandas as pd
import numpy as np
from tqdm import tqdm

from .optimizer import (
    Optimizer, OptimizationConfig, OptimizationResult,
    _init_worker, _evaluate_params
)
from ..backtesting import BacktestConfig
from ..risk import RiskConfig
from ..types import BacktestMetrics


class GridSearchOptimizer(Optimizer):
    """
    Grid search optimizer with multiprocessing support.

    Evaluates all parameter combinations (or a random sample)
    and returns the best performing parameters.
    """

    def __init__(
        self,
        config: OptimizationConfig,
        risk_config: Optional[RiskConfig] = None
    ) -> None:
        super().__init__(config)
        self.risk_config = risk_config or RiskConfig()

    def optimize(
        self,
        df: pd.DataFrame,
        strategy_class: type,
        backtest_config: BacktestConfig,
        param_grid: Dict[str, List[Any]],
        show_progress: bool = True
    ) -> OptimizationResult:
        """
        Run grid search optimization.

        Args:
            df: OHLCV DataFrame
            strategy_class: Strategy class to optimize
            backtest_config: Backtest configuration
            param_grid: Dictionary of parameter names to lists of values
            show_progress: Show progress bar

        Returns:
            OptimizationResult with best parameters and all results
        """
        # Generate parameter combinations
        combinations = self._generate_param_combinations(param_grid)

        if not combinations:
            raise ValueError("No parameter combinations to test")

        # Pickle DataFrame for worker processes
        df_pickle = pickle.dumps(df)

        results = []

        # Run optimization in parallel
        with ProcessPoolExecutor(
            max_workers=self.config.n_jobs,
            initializer=_init_worker,
            initargs=(df_pickle,)
        ) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    _evaluate_params,
                    params,
                    strategy_class,
                    backtest_config,
                    self.risk_config,
                    self.config.optimize_metric,
                    self.config.min_trades
                ): params
                for params in combinations
            }

            # Collect results with progress bar
            iterator = as_completed(futures)
            if show_progress:
                iterator = tqdm(
                    iterator,
                    total=len(futures),
                    desc="Optimizing"
                )

            for future in iterator:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    params = futures[future]
                    results.append({
                        "params": params,
                        "metric_value": float("-inf"),
                        "metrics": None,
                        "error": str(e)
                    })

        # Build results DataFrame
        results_df = self._build_results_dataframe(results)

        # Get best result
        valid_results = [r for r in results if r["metrics"] is not None]

        if not valid_results:
            raise ValueError("No valid optimization results")

        best_result = max(valid_results, key=lambda x: x["metric_value"])

        return OptimizationResult(
            best_params=best_result["params"],
            best_metrics=best_result["metrics"],
            all_results=results_df,
            total_combinations_tested=len(combinations),
            optimization_metric=self.config.optimize_metric,
        )

    def _build_results_dataframe(
        self,
        results: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Build sorted DataFrame from results."""
        rows = []

        for r in results:
            if r["metrics"] is None:
                continue

            row = {**r["params"]}
            metrics = r["metrics"]

            # Add all metrics
            row["profit_factor"] = metrics.profit_factor
            row["total_return_pct"] = metrics.total_return_pct
            row["win_rate"] = metrics.win_rate
            row["num_trades"] = metrics.num_trades
            row["max_drawdown_pct"] = metrics.max_drawdown_pct
            row["sharpe_ratio"] = metrics.sharpe_ratio
            row["sortino_ratio"] = metrics.sortino_ratio
            row["expectancy"] = metrics.expectancy

            rows.append(row)

        df = pd.DataFrame(rows)

        # Sort by optimization metric
        if len(df) > 0 and self.config.optimize_metric in df.columns:
            df = df.sort_values(
                self.config.optimize_metric,
                ascending=False
            ).reset_index(drop=True)

        return df

    def optimize_with_validation(
        self,
        train_df: pd.DataFrame,
        validation_df: pd.DataFrame,
        strategy_class: type,
        backtest_config: BacktestConfig,
        param_grid: Dict[str, List[Any]],
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Optimize on training data and validate on separate validation set.

        Returns dictionary with train results, validation results, and
        out-of-sample degradation metrics.
        """
        # Optimize on training data
        train_result = self.optimize(
            df=train_df,
            strategy_class=strategy_class,
            backtest_config=backtest_config,
            param_grid=param_grid,
            show_progress=show_progress
        )

        # Validate best parameters on validation data
        best_params = train_result.best_params

        # Create strategy with best params
        config_class = strategy_class.__annotations__.get("config", type(best_params))
        strategy = strategy_class(config_class(**best_params))

        # Run on validation data
        from ..backtesting import Backtester
        val_signals = strategy.generate_signals(validation_df.copy())
        backtester = Backtester(backtest_config, self.risk_config)
        val_result = backtester.run(val_signals)

        # Calculate degradation
        train_metric = getattr(train_result.best_metrics, self.config.optimize_metric, 0)
        val_metric = getattr(val_result.metrics, self.config.optimize_metric, 0)

        if train_metric != 0:
            degradation_pct = ((train_metric - val_metric) / abs(train_metric)) * 100
        else:
            degradation_pct = 0.0

        return {
            "best_params": best_params,
            "train_metrics": train_result.best_metrics,
            "validation_metrics": val_result.metrics,
            "train_metric_value": train_metric,
            "validation_metric_value": val_metric,
            "degradation_pct": degradation_pct,
            "all_train_results": train_result.all_results,
        }
