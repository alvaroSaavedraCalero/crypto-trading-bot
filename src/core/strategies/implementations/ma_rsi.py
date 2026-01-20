# src/core/strategies/implementations/ma_rsi.py
"""
Moving Average + RSI strategy.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..base import BaseStrategy, StrategyConfig
from ..registry import register_strategy


@dataclass
class MARSIConfig(StrategyConfig):
    """MA + RSI configuration."""
    fast_window: int = 10
    slow_window: int = 30
    rsi_window: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    use_rsi_filter: bool = True
    signal_mode: str = "cross"  # "cross" or "position"
    use_trend_filter: bool = False
    trend_ma_window: int = 200

    def __post_init__(self) -> None:
        if self.fast_window >= self.slow_window:
            raise ValueError("fast_window must be < slow_window")
        if not 0 < self.rsi_oversold < self.rsi_overbought < 100:
            raise ValueError("Invalid RSI levels")


@register_strategy("MA_RSI", MARSIConfig)
class MARSIStrategy(BaseStrategy[MARSIConfig]):
    """
    Moving Average Crossover with RSI filter.

    Entry signals:
    - Long: Fast MA crosses above Slow MA (+ RSI not overbought)
    - Short: Fast MA crosses below Slow MA (+ RSI not oversold)
    """

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate MA crossover signals."""
        self.validate_dataframe(df)
        data = df.copy()

        # Calculate MAs
        data["fast_ma"] = data["close"].ewm(
            span=self.config.fast_window,
            adjust=False
        ).mean()

        data["slow_ma"] = data["close"].ewm(
            span=self.config.slow_window,
            adjust=False
        ).mean()

        # Calculate RSI
        data = self.add_rsi(data, window=self.config.rsi_window)

        # Trend filter
        if self.config.use_trend_filter:
            data["trend_ma"] = data["close"].ewm(
                span=self.config.trend_ma_window,
                adjust=False
            ).mean()
        else:
            data["trend_ma"] = 0  # Placeholder

        # Signals
        data["signal"] = 0

        if self.config.signal_mode == "cross":
            # MA crossover signals
            data["ma_diff"] = data["fast_ma"] - data["slow_ma"]
            data["ma_diff_prev"] = data["ma_diff"].shift(1)

            # Bullish cross
            bull_cross = (data["ma_diff"] > 0) & (data["ma_diff_prev"] <= 0)

            # Bearish cross
            bear_cross = (data["ma_diff"] < 0) & (data["ma_diff_prev"] >= 0)

            # Apply RSI filter
            if self.config.use_rsi_filter:
                rsi_ok_long = data["rsi"] < self.config.rsi_overbought
                rsi_ok_short = data["rsi"] > self.config.rsi_oversold
            else:
                rsi_ok_long = True
                rsi_ok_short = True

            # Trend filter
            if self.config.use_trend_filter:
                trend_ok_long = data["close"] > data["trend_ma"]
                trend_ok_short = data["close"] < data["trend_ma"]
            else:
                trend_ok_long = True
                trend_ok_short = True

            # Long signal
            long_condition = bull_cross & rsi_ok_long & trend_ok_long
            data.loc[long_condition, "signal"] = 1

            # Short signal
            if self.config.allow_short:
                short_condition = bear_cross & rsi_ok_short & trend_ok_short
                data.loc[short_condition, "signal"] = -1

        else:  # position mode
            # Position above/below MA
            long_pos = data["fast_ma"] > data["slow_ma"]
            short_pos = data["fast_ma"] < data["slow_ma"]

            # Changes in position
            data.loc[long_pos & ~long_pos.shift(1).fillna(False), "signal"] = 1

            if self.config.allow_short:
                data.loc[short_pos & ~short_pos.shift(1).fillna(False), "signal"] = -1

        return data
