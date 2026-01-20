# src/core/types.py
"""
Core type definitions used across the trading system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional, List

import pandas as pd


class MarketType(Enum):
    """Supported market types."""
    CRYPTO = auto()
    FOREX = auto()
    STOCKS = auto()


class SignalType(Enum):
    """Trading signal types."""
    LONG = 1
    SHORT = -1
    NEUTRAL = 0


class OrderSide(Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class PositionSide(Enum):
    """Position direction."""
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class Symbol:
    """
    Represents a trading symbol/pair.

    Examples:
        - Crypto: Symbol("BTC", "USDT") -> "BTC/USDT"
        - Forex: Symbol("EUR", "USD") -> "EURUSD"
    """
    base: str
    quote: str
    market_type: MarketType = MarketType.CRYPTO

    def __str__(self) -> str:
        if self.market_type == MarketType.FOREX:
            return f"{self.base}{self.quote}"
        return f"{self.base}/{self.quote}"

    @classmethod
    def from_string(cls, symbol_str: str, market_type: MarketType = MarketType.CRYPTO) -> "Symbol":
        """Parse symbol from string format."""
        if "/" in symbol_str:
            base, quote = symbol_str.split("/")
        elif market_type == MarketType.FOREX and len(symbol_str) == 6:
            base, quote = symbol_str[:3], symbol_str[3:]
        else:
            raise ValueError(f"Cannot parse symbol: {symbol_str}")
        return cls(base=base.upper(), quote=quote.upper(), market_type=market_type)


@dataclass(frozen=True)
class Timeframe:
    """
    Represents a candlestick timeframe.

    Examples:
        - Timeframe(1, "m") -> 1 minute
        - Timeframe(4, "h") -> 4 hours
        - Timeframe(1, "d") -> 1 day
    """
    value: int
    unit: str  # "m", "h", "d", "w", "M"

    def __str__(self) -> str:
        return f"{self.value}{self.unit}"

    def to_minutes(self) -> int:
        """Convert timeframe to minutes."""
        multipliers = {"m": 1, "h": 60, "d": 1440, "w": 10080, "M": 43200}
        return self.value * multipliers.get(self.unit, 1)

    @classmethod
    def from_string(cls, tf_str: str) -> "Timeframe":
        """Parse timeframe from string like '15m', '1h', '1d'."""
        import re
        match = re.match(r"(\d+)([mhdwM])", tf_str)
        if not match:
            raise ValueError(f"Invalid timeframe format: {tf_str}")
        return cls(int(match.group(1)), match.group(2))


@dataclass
class OHLCV:
    """Single candlestick data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Trade:
    """
    Represents a completed trade.
    """
    id: str
    symbol: Symbol
    side: PositionSide
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    size: float
    stop_loss: float
    take_profit: float
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    fees: float = 0.0
    slippage: float = 0.0

    @property
    def is_closed(self) -> bool:
        return self.exit_time is not None

    @property
    def is_winner(self) -> bool:
        return self.pnl is not None and self.pnl > 0


@dataclass
class Position:
    """
    Represents an open position.
    """
    symbol: Symbol
    side: PositionSide
    entry_time: datetime
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    unrealized_pnl: float = 0.0


@dataclass
class BacktestMetrics:
    """
    Comprehensive backtesting metrics.
    """
    # Basic metrics
    total_return_pct: float = 0.0
    total_pnl: float = 0.0
    num_trades: int = 0

    # Win/Loss metrics
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    # Profit metrics
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0

    # Risk metrics
    max_drawdown_pct: float = 0.0
    max_drawdown_duration: int = 0  # in bars
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Trade metrics
    avg_trade_pnl: float = 0.0
    avg_winning_trade: float = 0.0
    avg_losing_trade: float = 0.0
    largest_winning_trade: float = 0.0
    largest_losing_trade: float = 0.0
    avg_trade_duration: float = 0.0  # in bars

    # Additional
    expectancy: float = 0.0
    recovery_factor: float = 0.0


@dataclass
class BacktestResult:
    """
    Complete backtest result with trades, equity curve, and metrics.
    """
    trades: List[Trade] = field(default_factory=list)
    equity_curve: Optional[pd.Series] = None
    metrics: BacktestMetrics = field(default_factory=BacktestMetrics)

    # Optimization metadata
    parameters: dict = field(default_factory=dict)
    symbol: Optional[Symbol] = None
    timeframe: Optional[Timeframe] = None
