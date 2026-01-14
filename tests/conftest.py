# tests/conftest.py
"""
Pytest configuration and shared fixtures for crypto-trading-bot tests.

This module provides:
- Sample OHLCV data fixtures
- Strategy configuration fixtures
- Backtest configuration fixtures
- Utility functions for test data generation
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any

import numpy as np
import pandas as pd
import pytest

from backtesting.engine import BacktestConfig, Backtester
from utils.risk import RiskManagementConfig


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """
    Generate sample OHLCV data for testing.
    Returns 500 rows of realistic-looking price data.
    """
    np.random.seed(42)
    n_rows = 500

    # Generate timestamps
    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_rows)]

    # Generate price data with realistic characteristics
    base_price = 100.0
    returns = np.random.normal(0, 0.02, n_rows)  # 2% daily volatility
    prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLC from close prices
    df = pd.DataFrame({
        "timestamp": timestamps,
        "close": prices,
    })

    # Add open, high, low with some randomness
    df["open"] = df["close"].shift(1).fillna(df["close"].iloc[0])
    df["high"] = df[["open", "close"]].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.005, n_rows)))
    df["low"] = df[["open", "close"]].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.005, n_rows)))
    df["volume"] = np.random.uniform(1000, 10000, n_rows)

    return df


@pytest.fixture
def small_ohlcv_data() -> pd.DataFrame:
    """Generate small OHLCV dataset for quick tests (50 rows)."""
    np.random.seed(42)
    n_rows = 50

    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_rows)]

    close = np.linspace(100, 110, n_rows) + np.random.normal(0, 1, n_rows)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "close": close,
    })

    df["open"] = df["close"].shift(1).fillna(df["close"].iloc[0])
    df["high"] = df[["open", "close"]].max(axis=1) * 1.005
    df["low"] = df[["open", "close"]].min(axis=1) * 0.995
    df["volume"] = 1000.0

    return df


@pytest.fixture
def trending_data() -> pd.DataFrame:
    """Generate trending (bullish) OHLCV data."""
    np.random.seed(42)
    n_rows = 200

    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_rows)]

    # Strong uptrend
    trend = np.linspace(0, 2, n_rows)  # 200% gain
    noise = np.random.normal(0, 0.01, n_rows)
    close = 100 * np.exp(trend + noise)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "close": close,
    })

    df["open"] = df["close"].shift(1).fillna(df["close"].iloc[0])
    df["high"] = df[["open", "close"]].max(axis=1) * 1.01
    df["low"] = df[["open", "close"]].min(axis=1) * 0.99
    df["volume"] = 1000.0

    return df


@pytest.fixture
def ranging_data() -> pd.DataFrame:
    """Generate ranging (sideways) OHLCV data."""
    np.random.seed(42)
    n_rows = 200

    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_rows)]

    # Sideways movement with oscillation
    t = np.linspace(0, 4 * np.pi, n_rows)
    close = 100 + 5 * np.sin(t) + np.random.normal(0, 0.5, n_rows)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "close": close,
    })

    df["open"] = df["close"].shift(1).fillna(df["close"].iloc[0])
    df["high"] = df[["open", "close"]].max(axis=1) * 1.005
    df["low"] = df[["open", "close"]].min(axis=1) * 0.995
    df["volume"] = 1000.0

    return df


@pytest.fixture
def backtest_config() -> BacktestConfig:
    """Default backtest configuration for tests."""
    return BacktestConfig(
        initial_capital=10000.0,
        sl_pct=0.02,
        tp_rr=2.0,
        fee_pct=0.001,
        allow_short=True,
        slippage_pct=0.0,
    )


@pytest.fixture
def risk_config() -> RiskManagementConfig:
    """Default risk management configuration for tests."""
    return RiskManagementConfig(
        risk_pct=0.02,
    )


@pytest.fixture
def backtester(backtest_config: BacktestConfig, risk_config: RiskManagementConfig) -> Backtester:
    """Default backtester instance for tests."""
    return Backtester(
        backtest_config=backtest_config,
        risk_config=risk_config,
    )


@pytest.fixture
def invalid_dataframe() -> pd.DataFrame:
    """DataFrame missing required columns for testing validation."""
    return pd.DataFrame({
        "timestamp": [datetime.now()],
        "close": [100.0],
        # Missing: open, high, low, volume
    })


@pytest.fixture
def dataframe_with_nans() -> pd.DataFrame:
    """DataFrame with NaN values for testing validation."""
    return pd.DataFrame({
        "timestamp": [datetime.now(), datetime.now()],
        "open": [100.0, np.nan],
        "high": [101.0, 101.0],
        "low": [99.0, 99.0],
        "close": [100.5, 100.5],
        "volume": [1000.0, 1000.0],
    })


@pytest.fixture
def strategy_configs() -> Dict[str, Any]:
    """
    Dictionary of default configs for all strategies.
    Useful for parametrized tests.
    """
    from strategies.ma_rsi_strategy import MovingAverageRSIStrategyConfig
    from strategies.supertrend_strategy import SupertrendStrategyConfig
    from strategies.bollinger_mean_reversion import BollingerMeanReversionStrategyConfig
    from strategies.keltner_breakout_strategy import KeltnerBreakoutStrategyConfig

    return {
        "MA_RSI": MovingAverageRSIStrategyConfig(),
        "SUPERTREND": SupertrendStrategyConfig(),
        "BOLLINGER_MR": BollingerMeanReversionStrategyConfig(),
        "KELTNER": KeltnerBreakoutStrategyConfig(),
    }
