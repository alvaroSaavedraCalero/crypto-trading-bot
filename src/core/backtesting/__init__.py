# src/core/backtesting/__init__.py
"""
Backtesting engine module.
"""

from .engine import Backtester, BacktestConfig
from .metrics import MetricsCalculator

__all__ = [
    "Backtester",
    "BacktestConfig",
    "MetricsCalculator",
]
