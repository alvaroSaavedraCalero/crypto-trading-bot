from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import BaseStrategy, StrategyMetadata


@dataclass
class PairsTradingConfig:
    """Configuration for Pairs Trading strategy.

    Attributes:
        pair_symbol: Ticker of the second asset (e.g., "ETH-USD").
        zscore_window: Window for z-score of the spread.
        entry_zscore: Z-score threshold for entry.
        exit_zscore: Z-score threshold for exit.
        stop_zscore: Z-score threshold for stop-loss.
        lookback: OLS regression lookback window.
    """

    pair_symbol: str = "ETH-USD"
    zscore_window: int = 20
    entry_zscore: float = 2.0
    exit_zscore: float = 0.5
    stop_zscore: float = 4.0
    lookback: int = 252

    def __post_init__(self) -> None:
        if not self.pair_symbol:
            raise ValueError("pair_symbol must not be empty")
        if self.zscore_window < 5:
            raise ValueError(f"zscore_window must be >= 5, got {self.zscore_window}")
        if self.entry_zscore <= self.exit_zscore:
            raise ValueError(
                f"entry_zscore ({self.entry_zscore}) must be > exit_zscore ({self.exit_zscore})"
            )
        if self.stop_zscore <= self.entry_zscore:
            raise ValueError(
                f"stop_zscore ({self.stop_zscore}) must be > entry_zscore ({self.entry_zscore})"
            )
        if self.lookback < 50:
            raise ValueError(f"lookback must be >= 50, got {self.lookback}")


class PairsTradingStrategy(BaseStrategy[PairsTradingConfig]):
    """Pairs Trading strategy using OLS spread and z-score.

    Fetches a second asset via yfinance, computes the OLS hedge ratio,
    and trades mean reversion of the spread.
    """

    name: str = "PAIRS_TRADING"

    def __init__(self, config: PairsTradingConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def _fetch_pair_data(self, start_date, end_date) -> pd.Series | None:
        """Fetch the pair asset's close prices using yfinance."""
        try:
            import yfinance as yf

            ticker = yf.Ticker(self.config.pair_symbol)
            pair_df = ticker.history(start=start_date, end=end_date)
            if pair_df.empty:
                return None
            return pair_df["Close"]
        except Exception:
            return None

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        c = self.config
        data = df.copy()

        if len(data) < c.lookback:
            data["signal"] = 0
            return data

        # Determine date range from the DataFrame
        if "timestamp" in data.columns:
            ts = pd.to_datetime(data["timestamp"])
            start_date = ts.min()
            end_date = ts.max()
        elif isinstance(data.index, pd.DatetimeIndex):
            start_date = data.index.min()
            end_date = data.index.max()
        else:
            data["signal"] = 0
            return data

        # Fetch pair data
        pair_close = self._fetch_pair_data(start_date, end_date)
        if pair_close is None or len(pair_close) < c.lookback:
            # Cannot compute spread without pair data; return neutral
            data["signal"] = 0
            return data

        # Align pair data with our data by date
        asset_a = data["close"].values
        n = len(asset_a)

        # Resample pair data to match length if needed
        pair_values = pair_close.values
        if len(pair_values) != n:
            # Simple interpolation to match lengths
            from scipy.interpolate import interp1d

            x_pair = np.linspace(0, 1, len(pair_values))
            x_target = np.linspace(0, 1, n)
            interp_func = interp1d(x_pair, pair_values, kind="linear", fill_value="extrapolate")
            pair_values = interp_func(x_target)

        data["pair_close"] = pair_values

        # Rolling OLS: spread = asset_A - beta * asset_B
        spread = np.full(n, np.nan)
        beta_arr = np.full(n, np.nan)

        for i in range(c.lookback, n):
            y = asset_a[i - c.lookback : i]
            x = pair_values[i - c.lookback : i]

            # OLS: y = beta * x + alpha
            x_mean = np.mean(x)
            y_mean = np.mean(y)
            cov_xy = np.mean((x - x_mean) * (y - y_mean))
            var_x = np.var(x)
            if var_x < 1e-10:
                continue
            beta = cov_xy / var_x
            beta_arr[i] = beta
            spread[i] = asset_a[i] - beta * pair_values[i]

        data["spread"] = spread
        data["beta"] = beta_arr

        # Z-score of spread
        spread_series = pd.Series(spread)
        rolling_mean = spread_series.rolling(window=c.zscore_window).mean()
        rolling_std = spread_series.rolling(window=c.zscore_window).std()
        data["spread_zscore"] = (spread_series - rolling_mean) / (rolling_std + 1e-10)

        data["signal"] = 0

        z = data["spread_zscore"]

        # Long spread (buy A): z < -entry_zscore
        data.loc[z < -c.entry_zscore, "signal"] = 1

        # Short spread (sell A): z > entry_zscore
        data.loc[z > c.entry_zscore, "signal"] = -1

        # Exit: z crosses back through exit_zscore (neutralize)
        data.loc[(z > -c.exit_zscore) & (z < c.exit_zscore), "signal"] = 0

        # Stop: extreme z-score
        data.loc[np.abs(z) > c.stop_zscore, "signal"] = 0

        # Signal strength
        data["signal_strength"] = np.clip(np.abs(z) / c.entry_zscore, 0.0, 1.0)
        data.loc[data["signal"] == 0, "signal_strength"] = 0.0

        return data
