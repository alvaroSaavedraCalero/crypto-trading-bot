"""Abstract base class for data providers."""

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


class DataProvider(ABC):
    """Abstract data provider for market data."""

    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 1000,
        period: str = "1y",
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a symbol.

        Args:
            symbol: Trading pair or ticker symbol.
            timeframe: Candle interval (e.g. "1m", "15m", "1h", "1d").
            limit: Maximum number of candles.
            period: Lookback period (e.g. "60d", "1y").

        Returns:
            DataFrame with columns [timestamp, open, high, low, close, volume]
            or None if data is unavailable.
        """
        ...

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch the current price for a symbol.

        Args:
            symbol: Trading pair or ticker symbol.

        Returns:
            Current price as float, or None if unavailable.
        """
        ...
