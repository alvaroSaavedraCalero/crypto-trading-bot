from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class OrderFlowConfig:
    """Configuration for Order Flow / Delta Volume strategy.

    Attributes:
        delta_window: Rolling window for delta moving average.
        divergence_lookback: Lookback for price/delta divergence detection.
        volume_ma_window: Window for volume moving average.
        min_delta_threshold: Minimum normalized delta to confirm signal.
    """

    delta_window: int = 14
    divergence_lookback: int = 20
    volume_ma_window: int = 20
    min_delta_threshold: float = 0.6

    def __post_init__(self) -> None:
        if self.delta_window < 2:
            raise ValueError(f"delta_window must be >= 2, got {self.delta_window}")
        if self.divergence_lookback < 5:
            raise ValueError(f"divergence_lookback must be >= 5, got {self.divergence_lookback}")
        if self.volume_ma_window < 2:
            raise ValueError(f"volume_ma_window must be >= 2, got {self.volume_ma_window}")
        if not 0 < self.min_delta_threshold <= 1:
            raise ValueError(
                f"min_delta_threshold must be in (0, 1], got {self.min_delta_threshold}"
            )


class OrderFlowStrategy(BaseStrategy[OrderFlowConfig]):
    """Order Flow / Delta Volume strategy.

    Approximates buy/sell volume from OHLC data, computes volume delta,
    and generates signals based on delta crossovers and divergences.
    """

    name: str = "ORDER_FLOW"

    def __init__(self, config: OrderFlowConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        min_periods = max(c.delta_window, c.volume_ma_window, c.divergence_lookback)
        if len(data) < min_periods:
            data["signal"] = 0
            return data

        # Approximate buy/sell volume
        hl_range = data["high"] - data["low"] + 1e-10
        buy_vol = data["volume"] * (data["close"] - data["low"]) / hl_range
        sell_vol = data["volume"] * (data["high"] - data["close"]) / hl_range

        data["delta"] = buy_vol - sell_vol
        data["cum_delta"] = data["delta"].rolling(window=c.divergence_lookback).sum()
        data["delta_ma"] = data["delta"].rolling(window=c.delta_window).mean()

        # Volume filter
        volume_ma = data["volume"].rolling(window=c.volume_ma_window).mean()
        above_avg_volume = data["volume"] > volume_ma

        # Delta MA crossover signals
        prev_delta_ma = data["delta_ma"].shift(1)
        cross_above_zero = (prev_delta_ma <= 0) & (data["delta_ma"] > 0)
        cross_below_zero = (prev_delta_ma >= 0) & (data["delta_ma"] < 0)

        data["signal"] = 0
        data.loc[cross_above_zero & above_avg_volume, "signal"] = 1
        data.loc[cross_below_zero & above_avg_volume, "signal"] = -1

        # Divergence detection: price makes new high but cum_delta is declining (bearish)
        price_high = data["close"].rolling(window=c.divergence_lookback).max()
        delta_high = data["cum_delta"].rolling(window=c.divergence_lookback).max()
        prev_price_high = data["close"].shift(1).rolling(window=c.divergence_lookback).max()
        prev_delta_high = data["cum_delta"].shift(1).rolling(window=c.divergence_lookback).max()

        bearish_div = (
            (data["close"] >= price_high)
            & (data["cum_delta"] < prev_delta_high)
            & above_avg_volume
        )

        # Price makes new low but cum_delta is rising (bullish divergence)
        price_low = data["close"].rolling(window=c.divergence_lookback).min()
        prev_delta_low = data["cum_delta"].shift(1).rolling(window=c.divergence_lookback).min()

        bullish_div = (
            (data["close"] <= price_low)
            & (data["cum_delta"] > prev_delta_low)
            & above_avg_volume
        )

        # Divergence overrides basic crossover
        data.loc[bearish_div & (data["signal"] != 1), "signal"] = -1
        data.loc[bullish_div & (data["signal"] != -1), "signal"] = 1

        # Signal strength: normalized absolute delta
        max_delta = data["delta_ma"].rolling(window=c.delta_window).apply(
            lambda x: np.max(np.abs(x)), raw=True
        )
        data["signal_strength"] = np.clip(
            np.abs(data["delta_ma"]) / (max_delta + 1e-10), 0.0, 1.0
        )
        data.loc[data["signal"] == 0, "signal_strength"] = 0.0

        return data
