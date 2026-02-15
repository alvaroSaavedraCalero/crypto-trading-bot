from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class GARCHConfig:
    """Configuration for GARCH Volatility Regime strategy.

    Attributes:
        garch_window: Historical window for GARCH fitting.
        trend_ema: EMA period for trend direction.
        refit_frequency: How often (in bars) to refit the GARCH model.
        vol_percentile: Percentile threshold for low/high vol regime classification.
    """

    garch_window: int = 252
    trend_ema: int = 50
    refit_frequency: int = 20
    vol_percentile: int = 50

    def __post_init__(self) -> None:
        if self.garch_window < 100:
            raise ValueError(f"garch_window must be >= 100, got {self.garch_window}")
        if self.trend_ema < 5:
            raise ValueError(f"trend_ema must be >= 5, got {self.trend_ema}")
        if self.refit_frequency < 1:
            raise ValueError(f"refit_frequency must be >= 1, got {self.refit_frequency}")
        if not 1 <= self.vol_percentile <= 99:
            raise ValueError(f"vol_percentile must be in [1, 99], got {self.vol_percentile}")


class GARCHStrategy(BaseStrategy[GARCHConfig]):
    """GARCH Volatility Regime strategy.

    Fits GARCH(1,1) to detect volatility regime transitions.
    Generates trend-following signals when volatility transitions from low to high.
    """

    name: str = "GARCH"

    def __init__(self, config: GARCHConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        if len(data) < c.garch_window + c.trend_ema:
            data["signal"] = 0
            return data

        # Log returns
        data["log_return"] = np.log(data["close"] / data["close"].shift(1))
        data["log_return"] = data["log_return"].fillna(0)

        # Scale returns to percentage for arch library numerical stability
        returns_pct = data["log_return"].values * 100

        # Trend EMA
        data["ema"] = data["close"].ewm(span=c.trend_ema, adjust=False).mean()

        n = len(data)
        cond_vol = np.full(n, np.nan)

        # Fit GARCH at refit_frequency intervals
        try:
            from arch import arch_model
        except ImportError:
            # arch library not available, return no signals
            data["signal"] = 0
            return data

        last_fit_vol = None
        for i in range(c.garch_window, n, c.refit_frequency):
            window_returns = returns_pct[max(0, i - c.garch_window) : i]

            try:
                model = arch_model(
                    window_returns,
                    vol="GARCH",
                    p=1,
                    q=1,
                    mean="Zero",
                    rescale=False,
                )
                result = model.fit(disp="off", show_warning=False)
                forecast = result.forecast(horizon=1)
                vol_forecast = np.sqrt(forecast.variance.values[-1, 0])
                last_fit_vol = vol_forecast
            except Exception:
                # On any GARCH fitting error, use last known or skip
                if last_fit_vol is not None:
                    vol_forecast = last_fit_vol
                else:
                    continue

            # Fill conditional volatility forward until next refit
            end = min(i + c.refit_frequency, n)
            cond_vol[i:end] = vol_forecast

        data["cond_vol"] = cond_vol

        # Determine vol regime using rolling percentile
        vol_series = pd.Series(cond_vol)
        vol_median = vol_series.expanding(min_periods=1).quantile(c.vol_percentile / 100.0)
        data["vol_regime"] = np.where(data["cond_vol"] > vol_median, "high", "low")

        # Detect regime transition: low -> high
        prev_regime = data["vol_regime"].shift(1)
        low_to_high = (prev_regime == "low") & (data["vol_regime"] == "high")

        data["signal"] = 0

        # Long: vol transition + close > EMA (bullish trend)
        data.loc[low_to_high & (data["close"] > data["ema"]), "signal"] = 1

        # Short: vol transition + close < EMA (bearish trend)
        data.loc[low_to_high & (data["close"] < data["ema"]), "signal"] = -1

        # Signal strength based on vol magnitude
        valid_vol = data["cond_vol"].notna()
        vol_max = data["cond_vol"].expanding().max()
        data["signal_strength"] = np.where(
            valid_vol, np.clip(data["cond_vol"] / (vol_max + 1e-10), 0.0, 1.0), 0.0
        )
        data.loc[data["signal"] == 0, "signal_strength"] = 0.0

        return data
