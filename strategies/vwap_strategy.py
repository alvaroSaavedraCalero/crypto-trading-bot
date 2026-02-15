from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class VWAPConfig:
    """Configuration for VWAP strategy.

    Attributes:
        std_bands: Number of standard deviations for upper/lower bands.
        volume_filter_mult: Volume must exceed volume_ma * this multiplier for signals.
        vwap_period: Rolling window for VWAP calculation.
    """

    std_bands: float = 2.0
    volume_filter_mult: float = 1.2
    vwap_period: int = 20

    def __post_init__(self) -> None:
        if self.std_bands <= 0:
            raise ValueError(f"std_bands must be > 0, got {self.std_bands}")
        if self.volume_filter_mult <= 0:
            raise ValueError(f"volume_filter_mult must be > 0, got {self.volume_filter_mult}")
        if self.vwap_period < 2:
            raise ValueError(f"vwap_period must be >= 2, got {self.vwap_period}")


class VWAPStrategy(BaseStrategy[VWAPConfig]):
    """VWAP (Volume Weighted Average Price) strategy with standard deviation bands.

    Long when close crosses above VWAP with high volume.
    Short when close crosses below VWAP with high volume.
    """

    name: str = "VWAP"

    def __init__(self, config: VWAPConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        if len(data) < c.vwap_period:
            data["signal"] = 0
            return data

        typical_price = (data["high"] + data["low"] + data["close"]) / 3
        tp_vol = typical_price * data["volume"]

        # Rolling VWAP
        cum_tp_vol = tp_vol.rolling(window=c.vwap_period).sum()
        cum_vol = data["volume"].rolling(window=c.vwap_period).sum()
        data["vwap"] = cum_tp_vol / (cum_vol + 1e-10)

        # Rolling standard deviation of typical price for bands
        rolling_std = typical_price.rolling(window=c.vwap_period).std()
        data["vwap_upper"] = data["vwap"] + c.std_bands * rolling_std
        data["vwap_lower"] = data["vwap"] - c.std_bands * rolling_std

        # Volume filter
        volume_ma = data["volume"].rolling(window=c.vwap_period).mean()
        high_volume = data["volume"] > volume_ma * c.volume_filter_mult

        # Crossover detection
        prev_close = data["close"].shift(1)
        prev_vwap = data["vwap"].shift(1)

        cross_above = (prev_close <= prev_vwap) & (data["close"] > data["vwap"])
        cross_below = (prev_close >= prev_vwap) & (data["close"] < data["vwap"])

        data["signal"] = 0
        data.loc[cross_above & high_volume, "signal"] = 1
        data.loc[cross_below & high_volume, "signal"] = -1

        # Signal strength: distance from VWAP normalized by rolling std
        distance = np.abs(data["close"] - data["vwap"])
        data["signal_strength"] = np.clip(distance / (rolling_std + 1e-10), 0.0, 1.0)
        data.loc[data["signal"] == 0, "signal_strength"] = 0.0

        # Clear signals where VWAP is not yet valid
        valid = data["vwap"].notna()
        data.loc[~valid, "signal"] = 0

        return data
