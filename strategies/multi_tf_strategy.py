from dataclasses import dataclass

import numpy as np
import pandas as pd
import ta

from .base import BaseStrategy, StrategyMetadata


@dataclass
class MultiTFConfig:
    """Configuration for Multi-Timeframe Confluence strategy.

    Attributes:
        higher_tf_multiplier: Multiplier for higher timeframe (e.g., 4 = 4x bars).
        trend_ema: EMA period for higher timeframe trend.
        entry_rsi_period: RSI period for entry signals.
        entry_rsi_oversold: RSI level for oversold condition.
        entry_rsi_overbought: RSI level for overbought condition.
    """

    higher_tf_multiplier: int = 4
    trend_ema: int = 50
    entry_rsi_period: int = 14
    entry_rsi_oversold: float = 30.0
    entry_rsi_overbought: float = 70.0

    def __post_init__(self) -> None:
        if self.higher_tf_multiplier < 2:
            raise ValueError(
                f"higher_tf_multiplier must be >= 2, got {self.higher_tf_multiplier}"
            )
        if self.trend_ema < 5:
            raise ValueError(f"trend_ema must be >= 5, got {self.trend_ema}")
        if self.entry_rsi_period < 2:
            raise ValueError(f"entry_rsi_period must be >= 2, got {self.entry_rsi_period}")
        if self.entry_rsi_oversold >= self.entry_rsi_overbought:
            raise ValueError(
                f"entry_rsi_oversold ({self.entry_rsi_oversold}) must be < "
                f"entry_rsi_overbought ({self.entry_rsi_overbought})"
            )


class MultiTFStrategy(BaseStrategy[MultiTFConfig]):
    """Multi-Timeframe Confluence strategy.

    Uses a simulated higher timeframe (via rolling aggregation) for trend
    determination, and the base timeframe RSI for entry timing.
    Only takes lower TF signals aligned with higher TF trend.
    """

    name: str = "MULTI_TF"

    def __init__(self, config: MultiTFConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        htf_window = c.higher_tf_multiplier
        min_required = htf_window * c.trend_ema + c.entry_rsi_period
        if len(data) < min_required:
            data["signal"] = 0
            return data

        # Simulate higher timeframe by rolling aggregation
        # Higher TF close = close sampled every htf_multiplier bars
        # Use rolling to get aggregated OHLCV for the higher timeframe
        htf_close = data["close"].rolling(window=htf_window).apply(lambda x: x.iloc[-1], raw=False)
        htf_high = data["high"].rolling(window=htf_window).max()
        htf_low = data["low"].rolling(window=htf_window).min()

        # Higher TF EMA for trend
        # Since each "htf bar" covers htf_multiplier lower bars, the EMA period
        # on the lower TF data should be trend_ema * htf_multiplier
        htf_ema_period = c.trend_ema * htf_window
        data["htf_ema"] = data["close"].ewm(span=htf_ema_period, adjust=False).mean()

        # Higher TF trend
        htf_bullish = data["close"] > data["htf_ema"]
        htf_bearish = data["close"] < data["htf_ema"]

        # Lower TF RSI for entry
        rsi_ind = ta.momentum.RSIIndicator(close=data["close"], window=c.entry_rsi_period)
        data["rsi"] = rsi_ind.rsi()

        # Entry signals
        rsi_oversold = data["rsi"] < c.entry_rsi_oversold
        rsi_overbought = data["rsi"] > c.entry_rsi_overbought

        # Previous RSI for crossover detection
        prev_rsi = data["rsi"].shift(1)
        rsi_cross_up = (prev_rsi <= c.entry_rsi_oversold) & (data["rsi"] > c.entry_rsi_oversold)
        rsi_cross_down = (prev_rsi >= c.entry_rsi_overbought) & (
            data["rsi"] < c.entry_rsi_overbought
        )

        data["signal"] = 0

        # Long: RSI exits oversold zone in bullish higher TF trend
        data.loc[rsi_cross_up & htf_bullish, "signal"] = 1

        # Short: RSI exits overbought zone in bearish higher TF trend
        data.loc[rsi_cross_down & htf_bearish, "signal"] = -1

        # Signal strength based on RSI distance from neutral
        data["signal_strength"] = np.clip(np.abs(data["rsi"] - 50) / 50, 0.0, 1.0)
        data.loc[data["signal"] == 0, "signal_strength"] = 0.0

        return data
