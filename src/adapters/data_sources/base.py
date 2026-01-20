# src/adapters/data_sources/base.py
"""
Base class for data source adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import pandas as pd

from ...core.types import Symbol, Timeframe, MarketType


@dataclass
class DataSourceConfig:
    """Base configuration for data sources."""
    cache_enabled: bool = True
    cache_dir: str = "./data/cache"
    timeout_seconds: int = 30


class DataSourceAdapter(ABC):
    """
    Abstract base class for all data source adapters.

    Provides a unified interface for fetching OHLCV data from
    various sources (exchanges, brokers, files).
    """

    market_type: MarketType = MarketType.CRYPTO

    def __init__(self, config: Optional[DataSourceConfig] = None) -> None:
        self.config = config or DataSourceConfig()

    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 5000
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data.

        Args:
            symbol: Trading pair
            timeframe: Candlestick timeframe
            start: Start datetime (optional)
            end: End datetime (optional)
            limit: Maximum number of candles

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        raise NotImplementedError

    @abstractmethod
    def get_available_symbols(self) -> List[Symbol]:
        """Return list of available symbols."""
        raise NotImplementedError

    @abstractmethod
    def get_available_timeframes(self) -> List[Timeframe]:
        """Return list of supported timeframes."""
        raise NotImplementedError

    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and normalize DataFrame format.

        Ensures:
        - Required columns exist
        - Timestamp is datetime type
        - Data is sorted by timestamp
        - No duplicate timestamps
        """
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Normalize
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").drop_duplicates("timestamp")
        df = df.reset_index(drop=True)

        # Ensure numeric types
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        return df
