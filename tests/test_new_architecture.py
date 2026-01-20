#!/usr/bin/env python3
"""
Tests for the new refactored architecture.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ============================================
# Test Core Types
# ============================================

class TestCoreTypes:
    """Test core type definitions."""

    def test_symbol_creation(self):
        """Test Symbol creation and string conversion."""
        from src.core.types import Symbol, MarketType

        # Crypto symbol
        crypto = Symbol("BTC", "USDT", MarketType.CRYPTO)
        assert str(crypto) == "BTC/USDT"

        # Forex symbol
        forex = Symbol("EUR", "USD", MarketType.FOREX)
        assert str(forex) == "EURUSD"

    def test_symbol_from_string(self):
        """Test Symbol parsing from string."""
        from src.core.types import Symbol, MarketType

        # Crypto format
        crypto = Symbol.from_string("BTC/USDT", MarketType.CRYPTO)
        assert crypto.base == "BTC"
        assert crypto.quote == "USDT"

        # Forex format
        forex = Symbol.from_string("EURUSD", MarketType.FOREX)
        assert forex.base == "EUR"
        assert forex.quote == "USD"

    def test_timeframe_creation(self):
        """Test Timeframe creation and conversion."""
        from src.core.types import Timeframe

        tf = Timeframe.from_string("15m")
        assert tf.value == 15
        assert tf.unit == "m"
        assert tf.to_minutes() == 15

        tf_hour = Timeframe.from_string("4h")
        assert tf_hour.to_minutes() == 240

    def test_trade_dataclass(self):
        """Test Trade dataclass."""
        from src.core.types import Trade, Symbol, PositionSide, MarketType

        trade = Trade(
            id="test123",
            symbol=Symbol("EUR", "USD", MarketType.FOREX),
            side=PositionSide.LONG,
            entry_time=datetime.now(),
            exit_time=datetime.now() + timedelta(hours=1),
            entry_price=1.1000,
            exit_price=1.1050,
            size=10000,
            stop_loss=1.0950,
            take_profit=1.1100,
            pnl=50.0,
        )

        assert trade.is_closed
        assert trade.is_winner


# ============================================
# Test Strategy Base
# ============================================

class TestStrategyBase:
    """Test BaseStrategy class."""

    def test_add_atr(self):
        """Test ATR calculation."""
        from src.core.strategies.base import BaseStrategy

        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=50, freq="h"),
            "open": np.random.uniform(100, 110, 50),
            "high": np.random.uniform(105, 115, 50),
            "low": np.random.uniform(95, 105, 50),
            "close": np.random.uniform(100, 110, 50),
            "volume": np.random.uniform(1000, 10000, 50),
        })

        result = BaseStrategy.add_atr(df, window=14)

        assert "atr" in result.columns
        assert result["atr"].iloc[13:].notna().all()

    def test_add_rsi(self):
        """Test RSI calculation."""
        from src.core.strategies.base import BaseStrategy

        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=50, freq="h"),
            "close": np.sin(np.linspace(0, 4*np.pi, 50)) * 10 + 100,
            "open": 100,
            "high": 110,
            "low": 90,
            "volume": 1000,
        })

        result = BaseStrategy.add_rsi(df, window=14)

        assert "rsi" in result.columns
        # RSI should be between 0 and 100
        valid_rsi = result["rsi"].dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_add_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        from src.core.strategies.base import BaseStrategy

        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=50, freq="h"),
            "close": np.random.uniform(100, 110, 50),
            "open": 100,
            "high": 110,
            "low": 90,
            "volume": 1000,
        })

        result = BaseStrategy.add_bollinger_bands(df, window=20, num_std=2.0)

        assert "bb_upper" in result.columns
        assert "bb_middle" in result.columns
        assert "bb_lower" in result.columns

        # Upper should be > middle > lower
        valid_idx = result["bb_middle"].notna()
        assert (result.loc[valid_idx, "bb_upper"] >= result.loc[valid_idx, "bb_middle"]).all()
        assert (result.loc[valid_idx, "bb_middle"] >= result.loc[valid_idx, "bb_lower"]).all()


# ============================================
# Test Strategy Implementations
# ============================================

class TestStrategies:
    """Test strategy implementations."""

    @pytest.fixture
    def sample_df(self):
        """Create sample OHLCV data."""
        np.random.seed(42)
        n = 500

        # Generate trending data
        trend = np.linspace(0, 10, n)
        noise = np.cumsum(np.random.randn(n) * 0.5)
        close = 100 + trend + noise

        return pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="15min"),
            "open": close - np.random.uniform(0, 1, n),
            "high": close + np.random.uniform(0, 2, n),
            "low": close - np.random.uniform(0, 2, n),
            "close": close,
            "volume": np.random.uniform(1000, 10000, n),
        })

    def test_supertrend_strategy(self, sample_df):
        """Test Supertrend strategy signal generation."""
        from src.core.strategies.implementations.supertrend import (
            SupertrendStrategy, SupertrendConfig
        )

        config = SupertrendConfig(
            atr_period=14,
            atr_multiplier=3.0,
            use_adx_filter=False,
            allow_short=True
        )

        strategy = SupertrendStrategy(config)
        result = strategy.generate_signals(sample_df)

        assert "signal" in result.columns
        # Should have some signals
        assert result["signal"].abs().sum() > 0
        # Signals should be -1, 0, or 1
        assert set(result["signal"].unique()).issubset({-1, 0, 1})

    def test_bollinger_mr_strategy(self, sample_df):
        """Test Bollinger Mean Reversion strategy."""
        from src.core.strategies.implementations.bollinger_mr import (
            BollingerMRStrategy, BollingerMRConfig
        )

        config = BollingerMRConfig(
            bb_window=20,
            bb_std=2.0,
            rsi_window=14,
            rsi_oversold=30.0,
            rsi_overbought=70.0,
            allow_short=True
        )

        strategy = BollingerMRStrategy(config)
        result = strategy.generate_signals(sample_df)

        assert "signal" in result.columns
        assert "bb_upper" in result.columns
        assert "bb_lower" in result.columns
        assert "rsi" in result.columns

    def test_keltner_strategy(self, sample_df):
        """Test Keltner Channel strategy."""
        from src.core.strategies.implementations.keltner import (
            KeltnerStrategy, KeltnerConfig
        )

        config = KeltnerConfig(
            kc_window=20,
            kc_mult=2.0,
            atr_window=14,
            allow_short=True
        )

        strategy = KeltnerStrategy(config)
        result = strategy.generate_signals(sample_df)

        assert "signal" in result.columns
        assert "kc_upper" in result.columns
        assert "kc_lower" in result.columns


# ============================================
# Test Backtesting
# ============================================

class TestBacktesting:
    """Test backtesting engine."""

    @pytest.fixture
    def sample_signals_df(self):
        """Create sample data with signals."""
        np.random.seed(42)
        n = 200

        close = 100 + np.cumsum(np.random.randn(n) * 0.5)

        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="15min"),
            "open": close - 0.1,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1000,
            "signal": 0,
        })

        # Add some signals
        df.loc[20, "signal"] = 1   # Long
        df.loc[50, "signal"] = -1  # Short
        df.loc[80, "signal"] = 1   # Long
        df.loc[120, "signal"] = -1  # Short

        return df

    def test_backtest_config_validation(self):
        """Test BacktestConfig validation."""
        from src.core.backtesting import BacktestConfig

        # Valid config
        config = BacktestConfig(
            initial_capital=10000.0,
            sl_pct=0.02,
            tp_rr=2.0
        )
        assert config.initial_capital == 10000.0

        # Invalid: negative capital
        with pytest.raises(ValueError):
            BacktestConfig(initial_capital=-1000)

        # Invalid: slippage too high
        with pytest.raises(ValueError):
            BacktestConfig(
                initial_capital=10000,
                slippage_pct=0.1  # 10% slippage
            )

    def test_backtester_run(self, sample_signals_df):
        """Test backtester execution."""
        from src.core.backtesting import Backtester, BacktestConfig
        from src.core.risk import RiskConfig

        backtest_config = BacktestConfig(
            initial_capital=10000.0,
            sl_pct=0.02,
            tp_rr=2.0,
            fee_pct=0.001
        )

        risk_config = RiskConfig(risk_pct=0.01)

        backtester = Backtester(backtest_config, risk_config)
        result = backtester.run(sample_signals_df)

        assert result.trades is not None
        assert result.equity_curve is not None
        assert result.metrics is not None
        assert len(result.equity_curve) == len(sample_signals_df)

    def test_metrics_calculation(self, sample_signals_df):
        """Test metrics are calculated correctly."""
        from src.core.backtesting import Backtester, BacktestConfig
        from src.core.risk import RiskConfig

        backtest_config = BacktestConfig(
            initial_capital=10000.0,
            sl_pct=0.05,
            tp_rr=2.0
        )

        backtester = Backtester(backtest_config, RiskConfig())
        result = backtester.run(sample_signals_df)

        metrics = result.metrics

        # Verify metrics exist
        assert hasattr(metrics, "total_return_pct")
        assert hasattr(metrics, "profit_factor")
        assert hasattr(metrics, "win_rate")
        assert hasattr(metrics, "max_drawdown_pct")
        assert hasattr(metrics, "sharpe_ratio")


# ============================================
# Test Risk Management
# ============================================

class TestRiskManagement:
    """Test risk management module."""

    def test_position_sizer_basic(self):
        """Test basic position sizing."""
        from src.core.risk import RiskConfig, PositionSizer

        config = RiskConfig(risk_pct=0.01)  # 1% risk
        sizer = PositionSizer(config)

        # Capital: 10000, Entry: 100, Stop: 98 (2% away)
        size = sizer.calculate(
            capital=10000,
            entry_price=100,
            stop_price=98
        )

        # Risk = 10000 * 0.01 = 100
        # Risk per unit = 100 - 98 = 2
        # Size = 100 / 2 = 50 (but may be limited by max_position_pct)
        # With default max_position_pct=0.25, max = 10000 * 0.25 / 100 = 25
        assert size == 25.0  # Limited by max position constraint

    def test_position_sizer_max_constraint(self):
        """Test position size max constraint."""
        from src.core.risk import RiskConfig, PositionSizer

        config = RiskConfig(
            risk_pct=0.05,  # 5% risk (large)
            max_position_pct=0.1  # Max 10% position
        )
        sizer = PositionSizer(config)

        size = sizer.calculate(
            capital=10000,
            entry_price=100,
            stop_price=99  # Only 1% away
        )

        # Without constraint: 500 / 1 = 500 units = $50,000
        # With 10% max position: max = 10000 * 0.1 / 100 = 10 units
        assert size == 10.0


# ============================================
# Test Data Adapters
# ============================================

class TestDataAdapters:
    """Test data source adapters."""

    def test_symbol_formatting(self):
        """Test symbol formatting for different markets."""
        from src.core.types import Symbol, MarketType
        from src.adapters.data_sources.fxcm import FXCMAdapter

        adapter = FXCMAdapter()

        forex_symbol = Symbol("EUR", "USD", MarketType.FOREX)
        formatted = adapter._format_symbol(forex_symbol)

        assert formatted == "EURUSD"

    def test_timeframe_conversion(self):
        """Test timeframe conversion."""
        from src.core.types import Timeframe
        from src.adapters.data_sources.fxcm import FXCMAdapter

        adapter = FXCMAdapter()

        tf = Timeframe.from_string("15m")
        fxcm_tf = adapter._format_timeframe(tf)

        assert fxcm_tf == "m15"


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
