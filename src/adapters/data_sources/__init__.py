# src/adapters/data_sources/__init__.py
"""
Data source adapters for various markets.
"""

from .base import DataSourceAdapter, DataSourceConfig
from .fxcm import FXCMAdapter, FXCMConfig
from .binance import BinanceAdapter
from .csv_loader import CSVDataLoader
from .factory import DataSourceFactory

__all__ = [
    "DataSourceAdapter",
    "DataSourceConfig",
    "FXCMAdapter",
    "FXCMConfig",
    "BinanceAdapter",
    "CSVDataLoader",
    "DataSourceFactory",
]
