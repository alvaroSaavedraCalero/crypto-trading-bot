# src/adapters/data_sources/binance.py
"""
Binance data adapter for cryptocurrency market data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List

import pandas as pd

from .base import DataSourceAdapter, DataSourceConfig
from ...core.types import Symbol, Timeframe, MarketType


@dataclass
class BinanceConfig(DataSourceConfig):
    """Binance-specific configuration."""
    # Use CCXT by default (no API key required for public data)
    use_ccxt: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class BinanceAdapter(DataSourceAdapter):
    """
    Binance cryptocurrency data adapter.

    Uses CCXT library for reliable data fetching.
    No API key required for historical OHLCV data.
    """

    market_type = MarketType.CRYPTO

    def __init__(self, config: Optional[BinanceConfig] = None) -> None:
        super().__init__(config or BinanceConfig())
        self.config: BinanceConfig = self.config
        self._exchange = None

    @property
    def exchange(self):
        """Lazy-load CCXT exchange."""
        if self._exchange is None:
            try:
                import ccxt
                self._exchange = ccxt.binance({
                    "enableRateLimit": True,
                    "options": {"defaultType": "spot"}
                })
            except ImportError:
                raise ImportError(
                    "CCXT is required for Binance adapter. "
                    "Install with: pip install ccxt"
                )
        return self._exchange

    def fetch_ohlcv(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 5000
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Binance."""
        symbol_str = str(symbol)  # "BTC/USDT"
        tf_str = str(timeframe)    # "15m"

        # Calculate since timestamp
        since = None
        if start:
            since = int(start.timestamp() * 1000)

        # Fetch data in chunks if needed (Binance limit is 1000)
        all_data = []
        remaining = limit
        current_since = since

        while remaining > 0:
            chunk_limit = min(remaining, 1000)

            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol_str,
                timeframe=tf_str,
                since=current_since,
                limit=chunk_limit
            )

            if not ohlcv:
                break

            all_data.extend(ohlcv)
            remaining -= len(ohlcv)

            if len(ohlcv) < chunk_limit:
                break

            # Update since for next chunk
            current_since = ohlcv[-1][0] + 1

        if not all_data:
            raise ValueError(f"No data returned for {symbol_str}")

        # Convert to DataFrame
        df = pd.DataFrame(
            all_data,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # Filter by end date
        if end:
            df = df[df["timestamp"] <= end]

        return self.validate_dataframe(df)

    def get_available_symbols(self) -> List[Symbol]:
        """Return popular trading pairs."""
        pairs = [
            ("BTC", "USDT"), ("ETH", "USDT"), ("BNB", "USDT"),
            ("SOL", "USDT"), ("XRP", "USDT"), ("ADA", "USDT"),
            ("DOGE", "USDT"), ("DOT", "USDT"), ("MATIC", "USDT"),
        ]
        return [Symbol(base, quote, MarketType.CRYPTO) for base, quote in pairs]

    def get_available_timeframes(self) -> List[Timeframe]:
        """Return supported timeframes."""
        timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        return [Timeframe.from_string(tf) for tf in timeframes]
