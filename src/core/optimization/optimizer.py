# src/core/optimization/optimizer.py
"""
Base optimizer class with multiprocessing support.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional, Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial

import pandas as pd
import numpy as np

from ..types import BacktestResult, BacktestMetrics
from ..backtesting import Backtester, BacktestConfig
from ..strategies import BaseStrategy


@dataclass
class OptimizationConfig:
    """
    Configuration for optimization runs.
    """
    # Parallel processing
    n_jobs: int = -1  # -1 = use all cores
    max_combinations: int = 5000  # Max parameter combinations to test

    # Optimization criteria
    optimize_metric: str = "profit_factor"  # Metric to maximize
    min_trades: int = 10  # Minimum trades required

    # Sampling
    use_random_sampling: bool = True  # Use random sampling if > max_combinations
    random_seed: Optional[int] = 42

    def __post_init__(self) -> None:
        if self.n_jobs == -1:
            self.n_jobs = mp.cpu_count()

        valid_metrics = {
            "profit_factor", "total_return_pct", "sharpe_ratio",
            "sortino_ratio", "win_rate", "expectancy", "calmar_ratio"
        }
        if self.optimize_metric not in valid_metrics:
            raise ValueError(f"optimize_metric must be one of {valid_metrics}")


@dataclass
class OptimizationResult:
    """
    Result of an optimization run.
    """
    best_params: Dict[str, Any]
    best_metrics: BacktestMetrics
    all_results: pd.DataFrame  # All tested combinations with metrics
    total_combinations_tested: int
    optimization_metric: str

    def top_n(self, n: int = 10) -> pd.DataFrame:
        """Return top N parameter combinations."""
        return self.all_results.head(n)

    def save_to_csv(self, filepath: str) -> None:
        """Save all results to CSV."""
        self.all_results.to_csv(filepath, index=False)


class Optimizer(ABC):
    """
    Abstract base optimizer class.
    """

    def __init__(self, config: OptimizationConfig) -> None:
        self.config = config

    @abstractmethod
    def optimize(
        self,
        df: pd.DataFrame,
        strategy_class: type,
        backtest_config: BacktestConfig,
        param_grid: Dict[str, List[Any]]
    ) -> OptimizationResult:
        """Run optimization."""
        raise NotImplementedError

    def _generate_param_combinations(
        self,
        param_grid: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """Generate all parameter combinations from grid."""
        import itertools

        keys = list(param_grid.keys())
        values = list(param_grid.values())

        combinations = [
            dict(zip(keys, combo))
            for combo in itertools.product(*values)
        ]

        # Sample if too many combinations
        if len(combinations) > self.config.max_combinations:
            if self.config.use_random_sampling:
                np.random.seed(self.config.random_seed)
                indices = np.random.choice(
                    len(combinations),
                    size=self.config.max_combinations,
                    replace=False
                )
                combinations = [combinations[i] for i in indices]
            else:
                combinations = combinations[:self.config.max_combinations]

        return combinations


# Global DataFrame for multiprocessing (avoids serialization overhead)
_GLOBAL_DF: Optional[pd.DataFrame] = None


def _init_worker(df_pickle: bytes) -> None:
    """Initialize worker process with shared DataFrame."""
    global _GLOBAL_DF
    import pickle
    _GLOBAL_DF = pickle.loads(df_pickle)


def _evaluate_params(
    params: Dict[str, Any],
    strategy_class: type,
    backtest_config: BacktestConfig,
    risk_config: Any,
    optimize_metric: str,
    min_trades: int
) -> Dict[str, Any]:
    """
    Evaluate a single parameter combination.
    Worker function for parallel execution.
    """
    global _GLOBAL_DF

    if _GLOBAL_DF is None:
        return {"params": params, "error": "No data available"}

    try:
        # Create strategy with parameters
        strategy = strategy_class(strategy_class.__annotations__.get("config", type(params))(**params))

        # Generate signals
        df_signals = strategy.generate_signals(_GLOBAL_DF.copy())

        # Run backtest
        from ..backtesting import Backtester
        backtester = Backtester(backtest_config, risk_config)
        result = backtester.run(df_signals)

        # Check minimum trades
        if result.metrics.num_trades < min_trades:
            return {
                "params": params,
                "metric_value": float("-inf"),
                "metrics": None,
                "error": f"Insufficient trades: {result.metrics.num_trades}"
            }

        # Get optimization metric
        metric_value = getattr(result.metrics, optimize_metric, 0.0)

        return {
            "params": params,
            "metric_value": metric_value,
            "metrics": result.metrics,
            "error": None
        }

    except Exception as e:
        return {
            "params": params,
            "metric_value": float("-inf"),
            "metrics": None,
            "error": str(e)
        }
