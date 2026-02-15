from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class MeanReversionConfig:
    """Configuration for Mean Reversion Statistical strategy.

    Attributes:
        hurst_window: Window for rolling Hurst exponent (R/S analysis).
        zscore_window: Window for z-score calculation.
        zscore_entry: Z-score threshold for entry signals.
        zscore_exit: Z-score threshold for exit signals.
        use_adf: Whether to use ADF test for stationarity confirmation.
        adf_pvalue: Maximum ADF p-value to consider series mean-reverting.
    """

    hurst_window: int = 100
    zscore_window: int = 20
    zscore_entry: float = 2.0
    zscore_exit: float = 0.5
    use_adf: bool = True
    adf_pvalue: float = 0.05

    def __post_init__(self) -> None:
        if self.hurst_window < 20:
            raise ValueError(f"hurst_window must be >= 20, got {self.hurst_window}")
        if self.zscore_window < 5:
            raise ValueError(f"zscore_window must be >= 5, got {self.zscore_window}")
        if self.zscore_entry <= self.zscore_exit:
            raise ValueError(
                f"zscore_entry ({self.zscore_entry}) must be > zscore_exit ({self.zscore_exit})"
            )
        if not 0 < self.adf_pvalue < 1:
            raise ValueError(f"adf_pvalue must be between 0 and 1, got {self.adf_pvalue}")


def _hurst_rs(series: np.ndarray) -> float:
    """Compute Hurst exponent using R/S analysis."""
    n = len(series)
    if n < 20:
        return 0.5

    max_k = min(n // 2, 50)
    if max_k < 4:
        return 0.5

    rs_list = []
    ns_list = []

    for k in range(4, max_k + 1):
        rs_values = []
        for start in range(0, n - k + 1, k):
            segment = series[start : start + k]
            mean_seg = np.mean(segment)
            deviations = segment - mean_seg
            cumdev = np.cumsum(deviations)
            r = np.max(cumdev) - np.min(cumdev)
            s = np.std(segment, ddof=1)
            if s > 1e-10:
                rs_values.append(r / s)
        if rs_values:
            rs_list.append(np.mean(rs_values))
            ns_list.append(k)

    if len(rs_list) < 2:
        return 0.5

    log_ns = np.log(ns_list)
    log_rs = np.log(rs_list)

    # Linear regression to estimate H
    coeffs = np.polyfit(log_ns, log_rs, 1)
    return float(np.clip(coeffs[0], 0.0, 1.0))


class MeanReversionStrategy(BaseStrategy[MeanReversionConfig]):
    """Mean Reversion Statistical strategy.

    Uses Hurst exponent to detect mean-reverting regimes, then trades
    z-score extremes. Optionally uses ADF test for confirmation.
    """

    name: str = "MEAN_REVERSION"

    def __init__(self, config: MeanReversionConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        if len(data) < c.hurst_window:
            data["signal"] = 0
            return data

        close = data["close"].values
        n = len(close)

        # Compute rolling Hurst exponent
        hurst = np.full(n, np.nan)
        for i in range(c.hurst_window, n):
            segment = close[i - c.hurst_window : i]
            hurst[i] = _hurst_rs(segment)
        data["hurst"] = hurst

        # Mean-reverting regime: Hurst < 0.45
        is_mean_reverting = data["hurst"] < 0.45

        # Optional ADF test
        if c.use_adf:
            try:
                from statsmodels.tsa.stattools import adfuller

                adf_pass = np.full(n, False)
                # Run ADF less frequently for performance (every 10 bars, carry forward)
                step = 10
                for i in range(c.hurst_window, n, step):
                    segment = close[max(0, i - c.hurst_window) : i]
                    try:
                        result = adfuller(segment, maxlag=5, autolag=None)
                        pval = result[1]
                        passed = pval < c.adf_pvalue
                    except Exception:
                        passed = False
                    end = min(i + step, n)
                    adf_pass[i:end] = passed

                data["adf_pass"] = adf_pass
                is_mean_reverting = is_mean_reverting & data["adf_pass"]
            except ImportError:
                pass  # statsmodels not available, skip ADF

        # Z-score
        rolling_mean = data["close"].rolling(window=c.zscore_window).mean()
        rolling_std = data["close"].rolling(window=c.zscore_window).std()
        data["zscore"] = (data["close"] - rolling_mean) / (rolling_std + 1e-10)

        data["signal"] = 0

        # Entry signals in mean-reverting regime
        data.loc[is_mean_reverting & (data["zscore"] < -c.zscore_entry), "signal"] = 1  # Oversold
        data.loc[is_mean_reverting & (data["zscore"] > c.zscore_entry), "signal"] = -1  # Overbought

        # Signal strength based on z-score magnitude
        data["signal_strength"] = np.clip(np.abs(data["zscore"]) / (c.zscore_entry * 2), 0.0, 1.0)
        data.loc[data["signal"] == 0, "signal_strength"] = 0.0

        return data
