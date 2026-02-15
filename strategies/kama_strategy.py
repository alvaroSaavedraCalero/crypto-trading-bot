from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class KAMAConfig:
    """Configuration for Kaufman Adaptive Moving Average strategy.

    Attributes:
        er_window: Efficiency Ratio lookback window.
        fast_sc: Fast smoothing constant period.
        slow_sc: Slow smoothing constant period.
    """

    er_window: int = 10
    fast_sc: int = 2
    slow_sc: int = 30

    def __post_init__(self) -> None:
        if self.er_window < 2:
            raise ValueError(f"er_window must be >= 2, got {self.er_window}")
        if self.fast_sc < 1:
            raise ValueError(f"fast_sc must be >= 1, got {self.fast_sc}")
        if self.slow_sc <= self.fast_sc:
            raise ValueError(f"slow_sc ({self.slow_sc}) must be > fast_sc ({self.fast_sc})")


class KAMAStrategy(BaseStrategy[KAMAConfig]):
    """Kaufman Adaptive Moving Average (KAMA) strategy.

    KAMA adapts its smoothing based on market efficiency.
    Long when close crosses above KAMA with positive slope.
    Short when close crosses below KAMA with negative slope.
    """

    name: str = "KAMA"

    def __init__(self, config: KAMAConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        if len(data) < c.er_window + 1:
            data["signal"] = 0
            return data

        close = data["close"].values
        n = len(close)

        fast_alpha = 2.0 / (c.fast_sc + 1)
        slow_alpha = 2.0 / (c.slow_sc + 1)

        kama = np.full(n, np.nan)

        # Compute KAMA iteratively
        # Start KAMA at the first valid index (er_window)
        kama[c.er_window] = close[c.er_window]

        for i in range(c.er_window + 1, n):
            # Direction: abs change over er_window
            direction = abs(close[i] - close[i - c.er_window])
            # Volatility: sum of abs day-to-day changes over er_window
            volatility = np.sum(np.abs(np.diff(close[i - c.er_window : i + 1])))

            if volatility == 0:
                er = 0.0
            else:
                er = direction / volatility

            sc = (er * (fast_alpha - slow_alpha) + slow_alpha) ** 2
            kama[i] = kama[i - 1] + sc * (close[i] - kama[i - 1])

        data["kama"] = kama
        data["kama_slope"] = data["kama"] - data["kama"].shift(1)

        # Crossover detection
        prev_close = data["close"].shift(1)
        prev_kama = data["kama"].shift(1)

        cross_above = (prev_close <= prev_kama) & (data["close"] > data["kama"])
        cross_below = (prev_close >= prev_kama) & (data["close"] < data["kama"])

        data["signal"] = 0
        data.loc[cross_above & (data["kama_slope"] > 0), "signal"] = 1
        data.loc[cross_below & (data["kama_slope"] < 0), "signal"] = -1

        # Signal strength based on efficiency ratio magnitude
        valid = data["kama"].notna()
        data.loc[~valid, "signal"] = 0

        return data
