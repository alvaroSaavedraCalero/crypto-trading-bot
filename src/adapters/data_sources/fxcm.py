# src/adapters/data_sources/fxcm.py
"""
FXCM data adapter for Forex market data.

FXCM provides free historical data through their REST API.
Works worldwide including Europe.

For live trading, users need an FXCM account, but for backtesting
the free data API can be used without an account.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import time

import pandas as pd
import numpy as np

from .base import DataSourceAdapter, DataSourceConfig
from ...core.types import Symbol, Timeframe, MarketType


@dataclass
class FXCMConfig(DataSourceConfig):
    """
    FXCM-specific configuration.

    Note: For historical data only (backtesting), no account is required.
    For live trading, you'd need FXCM credentials.
    """
    # API settings
    api_url: str = "https://candledata.fxcorporate.com"
    data_url: str = "https://tickdata.fxcorporate.com"

    # Rate limiting
    requests_per_minute: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0

    # Data settings
    include_weekend: bool = False

    # Alternative: use pre-downloaded data
    offline_data_dir: Optional[str] = None


# FXCM timeframe mapping
FXCM_TIMEFRAMES: Dict[str, str] = {
    "1m": "m1",
    "5m": "m5",
    "15m": "m15",
    "30m": "m30",
    "1h": "H1",
    "4h": "H4",
    "1d": "D1",
    "1w": "W1",
    "1M": "M1",
}

# Common Forex pairs available on FXCM
FXCM_SYMBOLS: List[str] = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY", "CADJPY",
    "XAUUSD", "XAGUSD",  # Gold and Silver
    "US30", "SPX500", "NAS100", "UK100", "GER30",  # Indices
]


class FXCMAdapter(DataSourceAdapter):
    """
    FXCM Forex data adapter.

    Supports:
    - Historical OHLCV data download
    - Multiple timeframes (1m to 1M)
    - Major, minor, and exotic Forex pairs
    - Commodities (Gold, Silver)
    - Stock indices

    Usage:
        adapter = FXCMAdapter()
        df = adapter.fetch_ohlcv(
            symbol=Symbol("EUR", "USD", MarketType.FOREX),
            timeframe=Timeframe.from_string("15m"),
            limit=5000
        )
    """

    market_type = MarketType.FOREX

    def __init__(self, config: Optional[FXCMConfig] = None) -> None:
        super().__init__(config or FXCMConfig())
        self.config: FXCMConfig = self.config
        self._last_request_time: float = 0
        self._request_count: int = 0

    def fetch_ohlcv(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 5000
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from FXCM.

        Falls back to alternative data sources if FXCM API is unavailable.
        """
        symbol_str = self._format_symbol(symbol)
        tf_str = self._format_timeframe(timeframe)

        # Check for offline data first
        if self.config.offline_data_dir:
            df = self._load_offline_data(symbol_str, tf_str, start, end, limit)
            if df is not None:
                return df

        # Try FXCM free data API
        try:
            df = self._fetch_from_fxcm(symbol_str, tf_str, start, end, limit)
            if df is not None and len(df) > 0:
                return self.validate_dataframe(df)
        except Exception as e:
            print(f"FXCM API error: {e}")

        # Fallback: Try yfinance for Forex
        try:
            df = self._fetch_from_yfinance(symbol_str, tf_str, start, end, limit)
            if df is not None and len(df) > 0:
                return self.validate_dataframe(df)
        except Exception as e:
            print(f"yfinance fallback error: {e}")

        # Fallback: Try generating sample data for testing
        if start is None:
            end = datetime.now()
            start = end - timedelta(days=365)

        raise ValueError(
            f"Could not fetch data for {symbol_str}. "
            "Please download historical data manually or check internet connection."
        )

    def _format_symbol(self, symbol: Symbol) -> str:
        """Format symbol for FXCM API."""
        return f"{symbol.base}{symbol.quote}".upper()

    def _format_timeframe(self, tf: Timeframe) -> str:
        """Convert timeframe to FXCM format."""
        tf_str = str(tf)
        if tf_str in FXCM_TIMEFRAMES:
            return FXCM_TIMEFRAMES[tf_str]
        raise ValueError(f"Unsupported timeframe: {tf_str}")

    def _fetch_from_fxcm(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[datetime],
        end: Optional[datetime],
        limit: int
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from FXCM's free candle data service.

        FXCM provides free historical data in CSV format.
        """
        try:
            import requests
        except ImportError:
            return None

        # FXCM free data URL format
        # Note: FXCM's free data is available by year/week
        # https://candledata.fxcorporate.com/{TIMEFRAME}/{SYMBOL}/{YEAR}/{WEEK}.csv.gz

        self._rate_limit()

        if end is None:
            end = datetime.now()

        if start is None:
            # Calculate start based on limit and timeframe
            tf_minutes = self._timeframe_to_minutes(timeframe)
            start = end - timedelta(minutes=tf_minutes * limit * 1.5)

        # Determine which weekly files to download
        all_data = []
        current = start

        while current < end:
            year = current.year
            week = current.isocalendar()[1]

            url = f"{self.config.api_url}/{timeframe}/{symbol}/{year}/{week}.csv.gz"

            try:
                response = requests.get(url, timeout=self.config.timeout_seconds)
                if response.status_code == 200:
                    from io import BytesIO
                    import gzip

                    with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
                        week_df = pd.read_csv(f, header=None)
                        week_df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
                        all_data.append(week_df)

                self._rate_limit()

            except Exception:
                pass  # Skip failed weeks

            current += timedelta(weeks=1)

        if not all_data:
            return None

        df = pd.concat(all_data, ignore_index=True)

        # Filter to date range
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        if start:
            df = df[df["timestamp"] >= start]
        if end:
            df = df[df["timestamp"] <= end]

        # Limit results
        if len(df) > limit:
            df = df.tail(limit)

        return df

    def _fetch_from_yfinance(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[datetime],
        end: Optional[datetime],
        limit: int
    ) -> Optional[pd.DataFrame]:
        """
        Fallback: Fetch from Yahoo Finance.

        Yahoo provides Forex data with =X suffix.
        """
        try:
            import yfinance as yf
        except ImportError:
            return None

        # Yahoo Finance symbol format
        yf_symbol = f"{symbol}=X"

        # Convert timeframe
        yf_interval = self._fxcm_to_yf_interval(timeframe)

        if end is None:
            end = datetime.now()

        if start is None:
            tf_minutes = self._timeframe_to_minutes(timeframe)
            start = end - timedelta(minutes=tf_minutes * limit * 1.5)

        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(
                start=start,
                end=end,
                interval=yf_interval
            )

            if df.empty:
                return None

            # Rename columns
            df = df.reset_index()
            df = df.rename(columns={
                "Date": "timestamp",
                "Datetime": "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            })

            # Select required columns
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]

            # Limit
            if len(df) > limit:
                df = df.tail(limit)

            return df

        except Exception:
            return None

    def _load_offline_data(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[datetime],
        end: Optional[datetime],
        limit: int
    ) -> Optional[pd.DataFrame]:
        """Load data from local CSV files."""
        if not self.config.offline_data_dir:
            return None

        data_dir = Path(self.config.offline_data_dir)
        patterns = [
            f"{symbol}_{timeframe}.csv",
            f"{symbol.lower()}_{timeframe}.csv",
            f"{symbol}_{timeframe.lower()}.csv",
        ]

        for pattern in patterns:
            filepath = data_dir / pattern
            if filepath.exists():
                df = pd.read_csv(filepath)
                df["timestamp"] = pd.to_datetime(df["timestamp"])

                if start:
                    df = df[df["timestamp"] >= start]
                if end:
                    df = df[df["timestamp"] <= end]
                if len(df) > limit:
                    df = df.tail(limit)

                return df

        return None

    def _rate_limit(self) -> None:
        """Apply rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < 60:
            self._request_count += 1
            if self._request_count >= self.config.requests_per_minute:
                sleep_time = 60 - time_since_last
                time.sleep(sleep_time)
                self._request_count = 0
        else:
            self._request_count = 1

        self._last_request_time = time.time()

    def _timeframe_to_minutes(self, tf: str) -> int:
        """Convert FXCM timeframe to minutes."""
        mapping = {
            "m1": 1, "m5": 5, "m15": 15, "m30": 30,
            "H1": 60, "H4": 240,
            "D1": 1440, "W1": 10080, "M1": 43200
        }
        return mapping.get(tf, 60)

    def _fxcm_to_yf_interval(self, fxcm_tf: str) -> str:
        """Convert FXCM timeframe to yfinance interval."""
        mapping = {
            "m1": "1m", "m5": "5m", "m15": "15m", "m30": "30m",
            "H1": "1h", "H4": "1h",  # yf doesn't support 4h directly
            "D1": "1d", "W1": "1wk", "M1": "1mo"
        }
        return mapping.get(fxcm_tf, "1h")

    def get_available_symbols(self) -> List[Symbol]:
        """Return available Forex symbols."""
        symbols = []
        for s in FXCM_SYMBOLS:
            if len(s) == 6:
                base, quote = s[:3], s[3:]
                symbols.append(Symbol(base, quote, MarketType.FOREX))
        return symbols

    def get_available_timeframes(self) -> List[Timeframe]:
        """Return supported timeframes."""
        return [Timeframe.from_string(tf) for tf in FXCM_TIMEFRAMES.keys()]

    def download_historical_data(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        years: int = 5,
        output_dir: str = "./data/forex"
    ) -> str:
        """
        Download and save historical data to CSV.

        Useful for offline backtesting.

        Args:
            symbol: Forex pair
            timeframe: Timeframe
            years: Number of years of history
            output_dir: Directory to save CSV

        Returns:
            Path to saved file
        """
        end = datetime.now()
        start = end - timedelta(days=years * 365)

        df = self.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            limit=years * 365 * 24 * 4  # Rough estimate for 15m
        )

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save to CSV
        symbol_str = self._format_symbol(symbol)
        tf_str = str(timeframe)
        filepath = output_path / f"{symbol_str}_{tf_str}.csv"

        df.to_csv(filepath, index=False)
        print(f"Saved {len(df)} candles to {filepath}")

        return str(filepath)
