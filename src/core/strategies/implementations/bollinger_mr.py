# src/core/strategies/implementations/bollinger_mr.py
"""
Bollinger Bands Mean Reversion strategy.

Works well for ranging markets in both crypto and forex.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..base import BaseStrategy, StrategyConfig
from ..registry import register_strategy


@dataclass
class BollingerMRConfig(StrategyConfig):
    """Bollinger Mean Reversion configuration."""
    bb_window: int = 20
    bb_std: float = 2.0
    rsi_window: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    def __post_init__(self) -> None:
        if self.bb_window < 2:
            raise ValueError("bb_window must be >= 2")
        if self.bb_std <= 0:
            raise ValueError("bb_std must be > 0")
        if not 0 < self.rsi_oversold < self.rsi_overbought < 100:
            raise ValueError("Invalid RSI levels")


@register_strategy("BOLLINGER_MR", BollingerMRConfig)
class BollingerMRStrategy(BaseStrategy[BollingerMRConfig]):
    """
    Bollinger Bands Mean Reversion strategy.

    Entry signals:
    - Long: Price below lower band + RSI oversold
    - Short: Price above upper band + RSI overbought

    Exit: Mean reversion to middle band.
    """

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate mean reversion signals."""
        self.validate_dataframe(df)
        data = df.copy()

        # Add Bollinger Bands
        data = self.add_bollinger_bands(
            data,
            window=self.config.bb_window,
            num_std=self.config.bb_std
        )

        # Add RSI
        data = self.add_rsi(data, window=self.config.rsi_window)

        # Signals
        data["signal"] = 0

        # Long: Price below lower band AND RSI oversold
        long_condition = (
            (data["close"] < data["bb_lower"]) &
            (data["rsi"] < self.config.rsi_oversold)
        )
        data.loc[long_condition, "signal"] = 1

        # Short: Price above upper band AND RSI overbought
        if self.config.allow_short:
            short_condition = (
                (data["close"] > data["bb_upper"]) &
                (data["rsi"] > self.config.rsi_overbought)
            )
            data.loc[short_condition, "signal"] = -1

        return data
