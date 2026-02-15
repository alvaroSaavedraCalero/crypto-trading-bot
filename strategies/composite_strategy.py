from dataclasses import dataclass, field
from typing import List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class CompositeConfig:
    """Configuration for Composite (multi-strategy) strategy.

    Attributes:
        strategies: List of (strategy_type, config_dict) tuples.
        combination_mode: How to combine signals - "unanimous", "majority", "any", "weighted".
        weights: Optional weights for "weighted" mode (must match strategies length).
    """

    strategies: List[Tuple[str, dict]] = field(
        default_factory=lambda: [("MA_RSI", {}), ("SUPERTREND", {})]
    )
    combination_mode: Literal["unanimous", "majority", "any", "weighted"] = "majority"
    weights: Optional[List[float]] = None

    def __post_init__(self) -> None:
        if not self.strategies:
            raise ValueError("strategies list must not be empty")
        if self.combination_mode not in ("unanimous", "majority", "any", "weighted"):
            raise ValueError(
                f"combination_mode must be 'unanimous', 'majority', 'any', or 'weighted', "
                f"got {self.combination_mode}"
            )
        if self.combination_mode == "weighted":
            if self.weights is None:
                raise ValueError("weights must be provided when combination_mode is 'weighted'")
            if len(self.weights) != len(self.strategies):
                raise ValueError(
                    f"weights length ({len(self.weights)}) must match "
                    f"strategies length ({len(self.strategies)})"
                )
            if any(w < 0 for w in self.weights):
                raise ValueError("All weights must be >= 0")


class CompositeStrategy(BaseStrategy[CompositeConfig]):
    """Composite strategy that combines signals from multiple sub-strategies.

    Supports unanimous, majority, any, and weighted combination modes.
    """

    name: str = "COMPOSITE"

    def __init__(self, config: CompositeConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        # Import here to avoid circular imports
        from .registry import STRATEGY_REGISTRY

        c = self.config
        data = df.copy()

        # Run each sub-strategy
        all_signals = []
        for strategy_type, config_dict in c.strategies:
            if strategy_type not in STRATEGY_REGISTRY:
                raise ValueError(f"Unknown strategy type: {strategy_type}")

            strat_cls, cfg_cls = STRATEGY_REGISTRY[strategy_type]
            try:
                cfg = cfg_cls(**config_dict)
                strat = strat_cls(config=cfg)
                result = strat.generate_signals(df)
                all_signals.append(result["signal"].values)
            except Exception:
                # If a sub-strategy fails, use neutral signals
                all_signals.append(np.zeros(len(df)))

        if not all_signals:
            data["signal"] = 0
            return data

        signals_matrix = np.column_stack(all_signals)
        n_strategies = signals_matrix.shape[1]

        if c.combination_mode == "unanimous":
            # Signal only when ALL strategies agree
            combined = np.zeros(len(df))
            all_long = np.all(signals_matrix == 1, axis=1)
            all_short = np.all(signals_matrix == -1, axis=1)
            combined[all_long] = 1
            combined[all_short] = -1

        elif c.combination_mode == "majority":
            # Signal when >50% agree
            combined = np.zeros(len(df))
            long_count = np.sum(signals_matrix == 1, axis=1)
            short_count = np.sum(signals_matrix == -1, axis=1)
            threshold = n_strategies / 2

            combined[long_count > threshold] = 1
            combined[short_count > threshold] = -1

        elif c.combination_mode == "any":
            # Signal when at least one fires (priority to longs if conflict)
            combined = np.zeros(len(df))
            any_long = np.any(signals_matrix == 1, axis=1)
            any_short = np.any(signals_matrix == -1, axis=1)
            combined[any_short] = -1
            combined[any_long] = 1  # Long takes priority

        elif c.combination_mode == "weighted":
            weights = np.array(c.weights)
            weight_sum = np.sum(weights)
            if weight_sum < 1e-10:
                data["signal"] = 0
                return data

            weighted_signal = signals_matrix @ weights / weight_sum
            combined = np.zeros(len(df))
            combined[weighted_signal > 0.5] = 1
            combined[weighted_signal < -0.5] = -1

        else:
            combined = np.zeros(len(df))

        data["signal"] = combined.astype(int)

        # Signal strength: proportion of strategies agreeing with the final signal
        agreement = np.zeros(len(df))
        for i in range(len(df)):
            if combined[i] == 1:
                agreement[i] = np.sum(signals_matrix[i] == 1) / n_strategies
            elif combined[i] == -1:
                agreement[i] = np.sum(signals_matrix[i] == -1) / n_strategies
        data["signal_strength"] = agreement

        return data
