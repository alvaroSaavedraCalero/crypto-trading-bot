# src/core/strategies/implementations/keltner.py
"""
Keltner Channel Breakout strategy.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..base import BaseStrategy, StrategyConfig
from ..registry import register_strategy


@dataclass
class KeltnerConfig(StrategyConfig):
    """Keltner Channel configuration."""
    kc_window: int = 20
    kc_mult: float = 2.0
    atr_window: int = 14
    atr_min_percentile: float = 0.3
    use_trend_filter: bool = False
    trend_ema_window: int = 100
    side_mode: str = "both"  # "long", "short", "both"

    def __post_init__(self) -> None:
        if self.kc_window < 2:
            raise ValueError("kc_window must be >= 2")
        if self.kc_mult <= 0:
            raise ValueError("kc_mult must be > 0")


@register_strategy("KELTNER", KeltnerConfig)
class KeltnerStrategy(BaseStrategy[KeltnerConfig]):
    """
    Keltner Channel Breakout strategy.

    Entry signals:
    - Long: Price closes above upper Keltner band
    - Short: Price closes below lower Keltner band

    Optional volatility and trend filters.
    """

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate Keltner breakout signals."""
        self.validate_dataframe(df)
        data = df.copy()

        # Calculate EMA for middle line
        data["kc_middle"] = data["close"].ewm(
            span=self.config.kc_window,
            adjust=False
        ).mean()

        # Calculate ATR
        data = self.add_atr(data, self.config.atr_window, "atr")

        # Keltner bands
        data["kc_upper"] = data["kc_middle"] + (self.config.kc_mult * data["atr"])
        data["kc_lower"] = data["kc_middle"] - (self.config.kc_mult * data["atr"])

        # Volatility filter
        atr_threshold = data["atr"].rolling(100).quantile(self.config.atr_min_percentile)
        data["vol_ok"] = data["atr"] >= atr_threshold

        # Trend filter
        if self.config.use_trend_filter:
            data["trend_ema"] = data["close"].ewm(
                span=self.config.trend_ema_window,
                adjust=False
            ).mean()
            data["trend_up"] = data["close"] > data["trend_ema"]
            data["trend_down"] = data["close"] < data["trend_ema"]
        else:
            data["trend_up"] = True
            data["trend_down"] = True

        # Signals
        data["signal"] = 0

        # Long breakout
        if self.config.side_mode in ("long", "both"):
            long_condition = (
                (data["close"] > data["kc_upper"]) &
                data["vol_ok"] &
                data["trend_up"]
            )
            data.loc[long_condition, "signal"] = 1

        # Short breakout
        if self.config.side_mode in ("short", "both") and self.config.allow_short:
            short_condition = (
                (data["close"] < data["kc_lower"]) &
                data["vol_ok"] &
                data["trend_down"]
            )
            data.loc[short_condition, "signal"] = -1

        return data
