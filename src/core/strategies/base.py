# src/core/strategies/base.py
"""
Base strategy class with improved validation and common utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional, Set, Dict, Any

import pandas as pd
import numpy as np

from ..types import SignalType


@dataclass
class StrategyConfig:
    """Base configuration for all strategies."""
    allow_short: bool = True


@dataclass
class StrategyMetadata:
    """
    Strategy metadata for identification and logging.
    """
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    tags: list = field(default_factory=list)


ConfigT = TypeVar("ConfigT", bound=StrategyConfig)


class BaseStrategy(ABC, Generic[ConfigT]):
    """
    Abstract base class for all trading strategies.

    Features:
    - Generic configuration support
    - Automatic DataFrame validation
    - Signal generation interface
    - Common indicator calculations

    Subclasses must implement:
    - generate_signals(df) -> DataFrame with 'signal' column
    """

    # Required OHLCV columns - subclasses can extend
    REQUIRED_COLUMNS: Set[str] = {"timestamp", "open", "high", "low", "close", "volume"}

    def __init__(
        self,
        config: ConfigT,
        metadata: Optional[StrategyMetadata] = None
    ) -> None:
        self.config = config
        self.metadata = metadata or StrategyMetadata(name=self.__class__.__name__)
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate strategy configuration. Override for custom validation."""
        pass

    def validate_dataframe(self, df: pd.DataFrame) -> None:
        """
        Validate that DataFrame contains all required columns.

        Raises:
            ValueError: If required columns are missing.
        """
        required = self.required_columns()
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"[{self.metadata.name}] Missing required columns: {missing}"
            )

        if df.empty:
            raise ValueError(f"[{self.metadata.name}] DataFrame is empty")

    def required_columns(self) -> Set[str]:
        """
        Return set of required columns.
        Subclasses can override to add strategy-specific requirements.
        """
        return self.REQUIRED_COLUMNS.copy()

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from OHLCV data.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with 'signal' column added:
            - 1 for long entry
            - -1 for short entry
            - 0 for no signal

        Note:
            - Must NOT modify the original DataFrame
            - Should use df.copy() internally
        """
        raise NotImplementedError

    def generate_last_signal(self, df: pd.DataFrame) -> SignalType:
        """
        Get the latest signal for live trading.

        Args:
            df: DataFrame with recent OHLCV data

        Returns:
            SignalType enum value
        """
        result_df = self.generate_signals(df)

        if result_df.empty or "signal" not in result_df.columns:
            return SignalType.NEUTRAL

        last_signal = result_df["signal"].iloc[-1]

        try:
            signal_value = int(last_signal)
            return SignalType(signal_value)
        except (ValueError, TypeError):
            return SignalType.NEUTRAL

    # ========================================
    # Common Indicator Helpers
    # ========================================

    @staticmethod
    def add_atr(
        df: pd.DataFrame,
        window: int = 14,
        column_name: str = "atr"
    ) -> pd.DataFrame:
        """
        Add Average True Range (ATR) column to DataFrame.

        Args:
            df: DataFrame with high, low, close columns
            window: ATR lookback period
            column_name: Name for the ATR column

        Returns:
            DataFrame with ATR column added
        """
        result = df.copy()

        high = result["high"]
        low = result["low"]
        close = result["close"]

        # True Range calculation
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR as exponential moving average of TR
        result[column_name] = tr.ewm(span=window, adjust=False).mean()

        return result

    @staticmethod
    def add_ema(
        df: pd.DataFrame,
        column: str = "close",
        window: int = 20,
        output_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Add Exponential Moving Average column."""
        result = df.copy()
        name = output_name or f"ema_{window}"
        result[name] = result[column].ewm(span=window, adjust=False).mean()
        return result

    @staticmethod
    def add_sma(
        df: pd.DataFrame,
        column: str = "close",
        window: int = 20,
        output_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Add Simple Moving Average column."""
        result = df.copy()
        name = output_name or f"sma_{window}"
        result[name] = result[column].rolling(window=window).mean()
        return result

    @staticmethod
    def add_rsi(
        df: pd.DataFrame,
        window: int = 14,
        column: str = "close",
        output_name: str = "rsi"
    ) -> pd.DataFrame:
        """Add Relative Strength Index column."""
        result = df.copy()

        delta = result[column].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.ewm(span=window, adjust=False).mean()
        avg_loss = loss.ewm(span=window, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.inf)
        result[output_name] = 100 - (100 / (1 + rs))

        return result

    @staticmethod
    def add_bollinger_bands(
        df: pd.DataFrame,
        window: int = 20,
        num_std: float = 2.0,
        column: str = "close"
    ) -> pd.DataFrame:
        """Add Bollinger Bands columns (bb_upper, bb_middle, bb_lower)."""
        result = df.copy()

        sma = result[column].rolling(window=window).mean()
        std = result[column].rolling(window=window).std()

        result["bb_middle"] = sma
        result["bb_upper"] = sma + (std * num_std)
        result["bb_lower"] = sma - (std * num_std)

        return result

    def get_info(self) -> Dict[str, Any]:
        """Return strategy information dictionary."""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "description": self.metadata.description,
            "config": self.config.__dict__ if hasattr(self.config, "__dict__") else str(self.config),
            "required_columns": list(self.required_columns()),
        }
