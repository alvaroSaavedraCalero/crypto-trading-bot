from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class VolumeProfileConfig:
    """Configuration for Volume Profile strategy.

    Attributes:
        profile_window: Rolling window for volume profile calculation.
        price_buckets: Number of price bins for the volume profile.
        value_area_pct: Percentage of total volume to define the value area.
        mode: Trading mode - "mean_reversion" or "breakout".
    """

    profile_window: int = 20
    price_buckets: int = 50
    value_area_pct: float = 0.70
    mode: Literal["mean_reversion", "breakout"] = "mean_reversion"

    def __post_init__(self) -> None:
        if self.profile_window < 5:
            raise ValueError(f"profile_window must be >= 5, got {self.profile_window}")
        if self.price_buckets < 10:
            raise ValueError(f"price_buckets must be >= 10, got {self.price_buckets}")
        if not 0 < self.value_area_pct < 1:
            raise ValueError(
                f"value_area_pct must be between 0 and 1, got {self.value_area_pct}"
            )
        if self.mode not in ("mean_reversion", "breakout"):
            raise ValueError(f"mode must be 'mean_reversion' or 'breakout', got {self.mode}")


class VolumeProfileStrategy(BaseStrategy[VolumeProfileConfig]):
    """Volume Profile strategy.

    Computes rolling volume profiles to identify POC, VAH, and VAL.
    Trades based on price interaction with value area boundaries.
    """

    name: str = "VOLUME_PROFILE"

    def __init__(self, config: VolumeProfileConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def _compute_profile(
        self, prices: np.ndarray, volumes: np.ndarray, highs: np.ndarray, lows: np.ndarray
    ) -> tuple:
        """Compute POC, VAH, VAL for a price/volume window."""
        price_min = np.min(lows)
        price_max = np.max(highs)
        if price_max - price_min < 1e-10:
            mid = (price_min + price_max) / 2
            return mid, mid, mid

        bin_edges = np.linspace(price_min, price_max, self.config.price_buckets + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_volumes = np.zeros(self.config.price_buckets)

        # Distribute volume across bins based on where close price falls
        for price, vol in zip(prices, volumes):
            idx = np.searchsorted(bin_edges[1:], price, side="left")
            idx = min(idx, self.config.price_buckets - 1)
            bin_volumes[idx] += vol

        # POC: bin with highest volume
        poc_idx = np.argmax(bin_volumes)
        poc = bin_centers[poc_idx]

        # Value area: sort bins by volume desc, accumulate until threshold
        total_vol = np.sum(bin_volumes)
        if total_vol < 1e-10:
            return poc, price_max, price_min

        sorted_indices = np.argsort(bin_volumes)[::-1]
        cum_vol = 0.0
        va_bins = []
        for idx in sorted_indices:
            va_bins.append(idx)
            cum_vol += bin_volumes[idx]
            if cum_vol >= total_vol * self.config.value_area_pct:
                break

        va_bins_sorted = sorted(va_bins)
        vah = bin_centers[va_bins_sorted[-1]]
        val = bin_centers[va_bins_sorted[0]]

        return poc, vah, val

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        if len(data) < c.profile_window:
            data["signal"] = 0
            return data

        close = data["close"].values
        volume = data["volume"].values
        highs = data["high"].values
        lows = data["low"].values
        n = len(data)

        poc_arr = np.full(n, np.nan)
        vah_arr = np.full(n, np.nan)
        val_arr = np.full(n, np.nan)

        for i in range(c.profile_window, n):
            start = i - c.profile_window
            poc_arr[i], vah_arr[i], val_arr[i] = self._compute_profile(
                close[start:i], volume[start:i], highs[start:i], lows[start:i]
            )

        data["poc"] = poc_arr
        data["vah"] = vah_arr
        data["val"] = val_arr

        prev_close = data["close"].shift(1)
        volume_ma = data["volume"].rolling(window=c.profile_window).mean()
        high_volume = data["volume"] > volume_ma

        data["signal"] = 0

        if c.mode == "mean_reversion":
            # Long: close was below VAL and reclaims (crosses above)
            reclaim_val = (prev_close < data["val"]) & (data["close"] >= data["val"])
            # Short: close was above VAH and falls back (crosses below)
            reject_vah = (prev_close > data["vah"]) & (data["close"] <= data["vah"])

            data.loc[reclaim_val, "signal"] = 1
            data.loc[reject_vah, "signal"] = -1

        elif c.mode == "breakout":
            # Long: close breaks above VAH with high volume
            break_above = (prev_close <= data["vah"]) & (data["close"] > data["vah"])
            # Short: close breaks below VAL with high volume
            break_below = (prev_close >= data["val"]) & (data["close"] < data["val"])

            data.loc[break_above & high_volume, "signal"] = 1
            data.loc[break_below & high_volume, "signal"] = -1

        # Signal strength: distance from POC
        dist_from_poc = np.abs(data["close"] - data["poc"])
        va_range = data["vah"] - data["val"]
        data["signal_strength"] = np.clip(dist_from_poc / (va_range + 1e-10), 0.0, 1.0)
        data.loc[data["signal"] == 0, "signal_strength"] = 0.0

        valid = data["poc"].notna()
        data.loc[~valid, "signal"] = 0

        return data
