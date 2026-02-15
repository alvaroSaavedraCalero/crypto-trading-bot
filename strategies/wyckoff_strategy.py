from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class WyckoffConfig:
    """Configuration for Wyckoff strategy.

    Attributes:
        range_min_bars: Minimum number of bars to confirm a trading range.
        range_threshold_pct: Max range width as % of mid-price to qualify as consolidation.
        spring_depth_pct: How far below support the spring must dip (as % of price).
        volume_spike_mult: Volume multiplier to confirm spring/UTAD.
        confirmation_bars: Bars after spring/UTAD to confirm the move.
    """

    range_min_bars: int = 30
    range_threshold_pct: float = 0.05
    spring_depth_pct: float = 0.01
    volume_spike_mult: float = 2.0
    confirmation_bars: int = 3

    def __post_init__(self) -> None:
        if self.range_min_bars < 10:
            raise ValueError(f"range_min_bars must be >= 10, got {self.range_min_bars}")
        if self.range_threshold_pct <= 0:
            raise ValueError(
                f"range_threshold_pct must be > 0, got {self.range_threshold_pct}"
            )
        if self.spring_depth_pct <= 0:
            raise ValueError(f"spring_depth_pct must be > 0, got {self.spring_depth_pct}")
        if self.volume_spike_mult <= 1:
            raise ValueError(
                f"volume_spike_mult must be > 1, got {self.volume_spike_mult}"
            )
        if self.confirmation_bars < 1:
            raise ValueError(
                f"confirmation_bars must be >= 1, got {self.confirmation_bars}"
            )


class WyckoffStrategy(BaseStrategy[WyckoffConfig]):
    """Wyckoff accumulation/distribution strategy.

    Detects trading ranges, then looks for springs (false breakdowns)
    and upthrust after distribution (UTAD, false breakouts).
    """

    name: str = "WYCKOFF"

    def __init__(self, config: WyckoffConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        if len(data) < c.range_min_bars + c.confirmation_bars:
            data["signal"] = 0
            return data

        close = data["close"].values
        high = data["high"].values
        low = data["low"].values
        volume = data["volume"].values
        n = len(data)

        signals = np.zeros(n)

        # Volume moving average
        vol_ma = pd.Series(volume).rolling(window=c.range_min_bars).mean().values

        for i in range(c.range_min_bars, n):
            # Define the range over the lookback window
            window_start = i - c.range_min_bars
            window_high = np.max(high[window_start:i])
            window_low = np.min(low[window_start:i])
            mid_price = (window_high + window_low) / 2

            if mid_price < 1e-10:
                continue

            range_width = (window_high - window_low) / mid_price

            # Check if we're in a consolidation range
            if range_width > c.range_threshold_pct:
                continue

            support = window_low
            resistance = window_high

            # Spring detection: price dips below support then recovers
            spring_level = support * (1 - c.spring_depth_pct)
            is_volume_spike = volume[i] > vol_ma[i] * c.volume_spike_mult if not np.isnan(vol_ma[i]) else False

            if low[i] < support and low[i] >= spring_level and close[i] > support and is_volume_spike:
                # Spring: dipped below support but closed back above, with volume
                # Check confirmation: next bars should hold above support
                if i + c.confirmation_bars < n:
                    confirmed = all(
                        close[i + j] > support for j in range(1, c.confirmation_bars + 1)
                    )
                    if confirmed:
                        signals[i + c.confirmation_bars] = 1

            # UTAD detection: price pokes above resistance then falls back
            utad_level = resistance * (1 + c.spring_depth_pct)
            if high[i] > resistance and high[i] <= utad_level and close[i] < resistance and is_volume_spike:
                # UTAD: poked above resistance but closed back below, with volume
                if i + c.confirmation_bars < n:
                    confirmed = all(
                        close[i + j] < resistance for j in range(1, c.confirmation_bars + 1)
                    )
                    if confirmed:
                        signals[i + c.confirmation_bars] = -1

        data["signal"] = signals

        # Signal strength: based on volume spike magnitude
        data["signal_strength"] = 0.0
        vol_ma_series = pd.Series(vol_ma)
        spike_ratio = pd.Series(volume) / (vol_ma_series + 1e-10)
        data["signal_strength"] = np.where(
            data["signal"] != 0, np.clip(spike_ratio / (c.volume_spike_mult * 2), 0.0, 1.0), 0.0
        )

        return data
