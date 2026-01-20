# src/adapters/data_sources/factory.py
"""
Data source factory for creating appropriate adapters.
"""

from __future__ import annotations

from typing import Optional

from .base import DataSourceAdapter
from .fxcm import FXCMAdapter, FXCMConfig
from .binance import BinanceAdapter, BinanceConfig
from .csv_loader import CSVDataLoader, CSVConfig
from ...core.types import MarketType


class DataSourceFactory:
    """
    Factory for creating data source adapters.

    Usage:
        # For Forex
        adapter = DataSourceFactory.create(MarketType.FOREX)

        # For Crypto
        adapter = DataSourceFactory.create(MarketType.CRYPTO)

        # With custom config
        adapter = DataSourceFactory.create(
            MarketType.FOREX,
            config=FXCMConfig(offline_data_dir="./data/forex")
        )
    """

    @staticmethod
    def create(
        market_type: MarketType,
        config: Optional[object] = None,
        prefer_offline: bool = False
    ) -> DataSourceAdapter:
        """
        Create appropriate data source adapter.

        Args:
            market_type: Type of market (CRYPTO, FOREX)
            config: Optional adapter-specific config
            prefer_offline: If True, prefer CSV loader over live adapters

        Returns:
            DataSourceAdapter instance
        """
        if prefer_offline:
            return CSVDataLoader(config if isinstance(config, CSVConfig) else None)

        if market_type == MarketType.FOREX:
            return FXCMAdapter(config if isinstance(config, FXCMConfig) else None)

        elif market_type == MarketType.CRYPTO:
            return BinanceAdapter(config if isinstance(config, BinanceConfig) else None)

        else:
            raise ValueError(f"Unsupported market type: {market_type}")

    @staticmethod
    def create_forex(
        offline_data_dir: Optional[str] = None
    ) -> DataSourceAdapter:
        """Create Forex data adapter."""
        if offline_data_dir:
            return FXCMAdapter(FXCMConfig(offline_data_dir=offline_data_dir))
        return FXCMAdapter()

    @staticmethod
    def create_crypto() -> DataSourceAdapter:
        """Create cryptocurrency data adapter."""
        return BinanceAdapter()

    @staticmethod
    def create_csv(data_directory: str) -> CSVDataLoader:
        """Create CSV data loader."""
        return CSVDataLoader(CSVConfig(data_directory=data_directory))
