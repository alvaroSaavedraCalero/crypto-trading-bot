# src/core/strategies/implementations/supertrend.py
"""
Supertrend strategy implementation.

Works well for both crypto and forex trending markets.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import numpy as np

from ..base import BaseStrategy, StrategyConfig
from ..registry import register_strategy


@dataclass
class SupertrendConfig(StrategyConfig):
    """Supertrend strategy configuration."""
    atr_period: int = 14
    atr_multiplier: float = 3.0
    use_adx_filter: bool = False
    adx_period: int = 14
    adx_threshold: float = 20.0

    def __post_init__(self) -> None:
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.atr_multiplier <= 0:
            raise ValueError("atr_multiplier must be > 0")


@register_strategy("SUPERTREND", SupertrendConfig)
class SupertrendStrategy(BaseStrategy[SupertrendConfig]):
    """
    Supertrend trend-following strategy.

    Entry signals:
    - Long: Price crosses above Supertrend line
    - Short: Price crosses below Supertrend line

    Optional ADX filter to trade only in strong trends.
    """

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate Supertrend signals."""
        self.validate_dataframe(df)
        data = df.copy()

        # Calculate ATR
        data = self.add_atr(data, self.config.atr_period, "atr")

        # Calculate Supertrend
        hl2 = (data["high"] + data["low"]) / 2

        # Upper and lower bands
        data["basic_upper"] = hl2 + (self.config.atr_multiplier * data["atr"])
        data["basic_lower"] = hl2 - (self.config.atr_multiplier * data["atr"])

        # Final bands with proper trend continuation
        data["final_upper"] = data["basic_upper"]
        data["final_lower"] = data["basic_lower"]

        for i in range(1, len(data)):
            # Upper band
            if (data["basic_upper"].iloc[i] < data["final_upper"].iloc[i-1] or
                data["close"].iloc[i-1] > data["final_upper"].iloc[i-1]):
                data.loc[data.index[i], "final_upper"] = data["basic_upper"].iloc[i]
            else:
                data.loc[data.index[i], "final_upper"] = data["final_upper"].iloc[i-1]

            # Lower band
            if (data["basic_lower"].iloc[i] > data["final_lower"].iloc[i-1] or
                data["close"].iloc[i-1] < data["final_lower"].iloc[i-1]):
                data.loc[data.index[i], "final_lower"] = data["basic_lower"].iloc[i]
            else:
                data.loc[data.index[i], "final_lower"] = data["final_lower"].iloc[i-1]

        # Supertrend direction
        data["supertrend"] = np.nan
        data["direction"] = 1  # 1 = uptrend, -1 = downtrend

        for i in range(1, len(data)):
            if data["close"].iloc[i] > data["final_upper"].iloc[i-1]:
                data.loc[data.index[i], "direction"] = 1
            elif data["close"].iloc[i] < data["final_lower"].iloc[i-1]:
                data.loc[data.index[i], "direction"] = -1
            else:
                data.loc[data.index[i], "direction"] = data["direction"].iloc[i-1]

            if data["direction"].iloc[i] == 1:
                data.loc[data.index[i], "supertrend"] = data["final_lower"].iloc[i]
            else:
                data.loc[data.index[i], "supertrend"] = data["final_upper"].iloc[i]

        # Direction changes generate signals
        data["signal"] = 0
        data["dir_change"] = data["direction"].diff()

        # Long when direction changes to 1
        data.loc[data["dir_change"] == 2, "signal"] = 1

        # Short when direction changes to -1
        if self.config.allow_short:
            data.loc[data["dir_change"] == -2, "signal"] = -1

        # Optional ADX filter
        if self.config.use_adx_filter:
            data = self._add_adx(data)
            # Only keep signals where ADX > threshold
            weak_trend = data["adx"] < self.config.adx_threshold
            data.loc[weak_trend, "signal"] = 0

        return data

    def _add_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add ADX indicator."""
        period = self.config.adx_period

        # +DM and -DM
        df["plus_dm"] = df["high"].diff()
        df["minus_dm"] = -df["low"].diff()

        df.loc[df["plus_dm"] < 0, "plus_dm"] = 0
        df.loc[df["minus_dm"] < 0, "minus_dm"] = 0

        df.loc[df["plus_dm"] < df["minus_dm"], "plus_dm"] = 0
        df.loc[df["minus_dm"] < df["plus_dm"], "minus_dm"] = 0

        # Smoothed +DI and -DI
        tr = pd.concat([
            df["high"] - df["low"],
            abs(df["high"] - df["close"].shift(1)),
            abs(df["low"] - df["close"].shift(1))
        ], axis=1).max(axis=1)

        atr = tr.ewm(span=period, adjust=False).mean()
        plus_di = 100 * (df["plus_dm"].ewm(span=period, adjust=False).mean() / atr)
        minus_di = 100 * (df["minus_dm"].ewm(span=period, adjust=False).mean() / atr)

        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df["adx"] = dx.ewm(span=period, adjust=False).mean()

        return df
