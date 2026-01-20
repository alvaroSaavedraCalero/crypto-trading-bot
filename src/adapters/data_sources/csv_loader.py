# src/adapters/data_sources/csv_loader.py
"""
CSV data loader for offline backtesting.

Supports various CSV formats from popular data providers:
- HistData (free historical Forex data)
- Dukascopy (tick data)
- TradingView exports
- Generic OHLCV format
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

import pandas as pd

from .base import DataSourceAdapter, DataSourceConfig
from ...core.types import Symbol, Timeframe, MarketType


@dataclass
class CSVConfig(DataSourceConfig):
    """CSV loader configuration."""
    data_directory: str = "./data"
    date_format: Optional[str] = None  # Auto-detect if None
    delimiter: str = ","
    encoding: str = "utf-8"


class CSVDataLoader(DataSourceAdapter):
    """
    Load OHLCV data from CSV files.

    Supports multiple CSV formats:
    - Standard: timestamp,open,high,low,close,volume
    - HistData: Date,Time,Open,High,Low,Close,Volume
    - Dukascopy: Gmt time,Open,High,Low,Close,Volume
    - TradingView: time,open,high,low,close,volume
    """

    def __init__(self, config: Optional[CSVConfig] = None) -> None:
        super().__init__(config or CSVConfig())
        self.config: CSVConfig = self.config

    def fetch_ohlcv(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 5000
    ) -> pd.DataFrame:
        """Load OHLCV data from CSV file."""
        filepath = self._find_file(symbol, timeframe)

        if filepath is None:
            raise FileNotFoundError(
                f"No CSV file found for {symbol} {timeframe} "
                f"in {self.config.data_directory}"
            )

        df = self._load_csv(filepath)

        # Filter by date range
        if start:
            df = df[df["timestamp"] >= start]
        if end:
            df = df[df["timestamp"] <= end]

        # Limit results
        if len(df) > limit:
            df = df.tail(limit)

        return self.validate_dataframe(df)

    def _find_file(
        self,
        symbol: Symbol,
        timeframe: Timeframe
    ) -> Optional[Path]:
        """Find CSV file matching symbol and timeframe."""
        data_dir = Path(self.config.data_directory)

        if not data_dir.exists():
            return None

        symbol_str = str(symbol).replace("/", "")
        tf_str = str(timeframe)

        # Try various naming conventions
        patterns = [
            f"{symbol_str}_{tf_str}.csv",
            f"{symbol_str.lower()}_{tf_str}.csv",
            f"{symbol_str}_{tf_str.lower()}.csv",
            f"{symbol_str.upper()}_{tf_str.upper()}.csv",
            f"{symbol_str}.csv",
        ]

        for pattern in patterns:
            filepath = data_dir / pattern
            if filepath.exists():
                return filepath

        # Search subdirectories
        for csv_file in data_dir.rglob("*.csv"):
            name = csv_file.stem.lower()
            if symbol_str.lower() in name:
                return csv_file

        return None

    def _load_csv(self, filepath: Path) -> pd.DataFrame:
        """Load and normalize CSV file."""
        # Try to detect format
        df = pd.read_csv(
            filepath,
            delimiter=self.config.delimiter,
            encoding=self.config.encoding
        )

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        # Detect and rename columns
        column_mapping = self._detect_column_mapping(df.columns.tolist())
        df = df.rename(columns=column_mapping)

        # Parse timestamp
        df = self._parse_timestamp(df)

        # Ensure required columns
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                if col == "volume":
                    df["volume"] = 0
                else:
                    raise ValueError(f"Missing required column: {col}")

        return df[required]

    def _detect_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """Detect and create column mapping."""
        mapping = {}

        # Common variations
        timestamp_names = ["timestamp", "time", "date", "datetime", "gmt time"]
        open_names = ["open", "o"]
        high_names = ["high", "h"]
        low_names = ["low", "l"]
        close_names = ["close", "c"]
        volume_names = ["volume", "vol", "v", "tickqty"]

        for col in columns:
            col_lower = col.lower()

            if col_lower in timestamp_names:
                mapping[col] = "timestamp"
            elif col_lower in open_names:
                mapping[col] = "open"
            elif col_lower in high_names:
                mapping[col] = "high"
            elif col_lower in low_names:
                mapping[col] = "low"
            elif col_lower in close_names:
                mapping[col] = "close"
            elif col_lower in volume_names:
                mapping[col] = "volume"

        return mapping

    def _parse_timestamp(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse timestamp column with various formats."""
        if "timestamp" not in df.columns:
            # Try combining date and time columns
            if "date" in df.columns and "time" in df.columns:
                df["timestamp"] = df["date"] + " " + df["time"]
            else:
                raise ValueError("Cannot find timestamp column")

        # Try parsing with various formats
        formats = [
            None,  # Let pandas infer
            "%Y-%m-%d %H:%M:%S",
            "%Y.%m.%d %H:%M:%S",
            "%d.%m.%Y %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in formats:
            try:
                df["timestamp"] = pd.to_datetime(df["timestamp"], format=fmt)
                return df
            except Exception:
                continue

        raise ValueError("Could not parse timestamp column")

    def get_available_symbols(self) -> List[Symbol]:
        """Return symbols found in data directory."""
        symbols = []
        data_dir = Path(self.config.data_directory)

        if data_dir.exists():
            for csv_file in data_dir.rglob("*.csv"):
                name = csv_file.stem.upper()
                # Try to extract symbol from filename
                if len(name) >= 6:
                    # Assume format like EURUSD_15m
                    parts = name.split("_")
                    if parts:
                        sym = parts[0]
                        if len(sym) == 6:
                            base, quote = sym[:3], sym[3:]
                            symbols.append(Symbol(base, quote, MarketType.FOREX))

        return list(set(symbols))

    def get_available_timeframes(self) -> List[Timeframe]:
        """Return commonly supported timeframes."""
        return [Timeframe.from_string(tf) for tf in ["1m", "5m", "15m", "1h", "4h", "1d"]]

    def load_histdata_format(
        self,
        filepath: str,
        symbol: Symbol
    ) -> pd.DataFrame:
        """
        Load data in HistData.com format.

        HistData provides free Forex historical data.
        Download from: https://www.histdata.com/download-free-forex-data/
        """
        # HistData ASCII format: YYYYMMDD HHMMSS;OPEN;HIGH;LOW;CLOSE;VOLUME
        df = pd.read_csv(
            filepath,
            delimiter=";",
            header=None,
            names=["datetime", "open", "high", "low", "close", "volume"]
        )

        # Parse datetime
        df["timestamp"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
        df = df.drop("datetime", axis=1)

        return self.validate_dataframe(df)

    def load_dukascopy_format(
        self,
        filepath: str,
        symbol: Symbol
    ) -> pd.DataFrame:
        """
        Load data in Dukascopy format.

        Dukascopy provides free tick data.
        Download from: https://www.dukascopy.com/swiss/english/marketwatch/historical/
        """
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.lower().str.strip()

        # Dukascopy format: Gmt time,Open,High,Low,Close,Volume
        if "gmt time" in df.columns:
            df = df.rename(columns={"gmt time": "timestamp"})

        df["timestamp"] = pd.to_datetime(df["timestamp"])

        return self.validate_dataframe(df)
