# tests/test_all_strategies.py
"""
Comprehensive tests for all trading strategies.

Tests include:
- Signal generation validity
- Configuration validation
- Edge cases and error handling
- Integration with backtester
"""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np

from strategies.registry import STRATEGY_REGISTRY, create_strategy
from strategies.ma_rsi_strategy import (
    MovingAverageRSIStrategy,
    MovingAverageRSIStrategyConfig,
)
from strategies.supertrend_strategy import (
    SupertrendStrategy,
    SupertrendStrategyConfig,
)
from strategies.bollinger_mean_reversion import (
    BollingerMeanReversionStrategy,
    BollingerMeanReversionStrategyConfig,
)
from strategies.keltner_breakout_strategy import (
    KeltnerBreakoutStrategy,
    KeltnerBreakoutStrategyConfig,
)
from utils.validation import ValidationError


class TestStrategyRegistry:
    """Tests for the strategy registry and factory."""

    def test_registry_contains_expected_strategies(self):
        """Registry should contain all expected strategies."""
        expected = ["MA_RSI", "SUPERTREND", "BOLLINGER_MR", "KELTNER"]
        for name in expected:
            assert name in STRATEGY_REGISTRY, f"Strategy {name} not in registry"

    def test_create_strategy_with_valid_config(self):
        """Factory should create strategy with valid config."""
        config = SupertrendStrategyConfig()
        strategy = create_strategy("SUPERTREND", config)
        assert isinstance(strategy, SupertrendStrategy)

    def test_create_strategy_with_invalid_type(self):
        """Factory should raise error for unknown strategy type."""
        with pytest.raises(ValueError, match="no registrada"):
            create_strategy("UNKNOWN_STRATEGY", None)

    def test_create_strategy_with_wrong_config_type(self):
        """Factory should raise error for mismatched config type."""
        wrong_config = MovingAverageRSIStrategyConfig()
        with pytest.raises(TypeError, match="Config no válida"):
            create_strategy("SUPERTREND", wrong_config)


class TestMovingAverageRSIStrategy:
    """Tests for MA_RSI strategy."""

    def test_generate_signals_returns_dataframe(self, sample_ohlcv_data):
        """generate_signals should return a DataFrame with signal column."""
        config = MovingAverageRSIStrategyConfig()
        strategy = MovingAverageRSIStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert "signal" in result.columns

    def test_signals_are_valid_values(self, sample_ohlcv_data):
        """Signals should only be -1, 0, or 1."""
        config = MovingAverageRSIStrategyConfig()
        strategy = MovingAverageRSIStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert set(result["signal"].unique()).issubset({-1, 0, 1})

    def test_config_validation_fast_window_greater_than_slow(self):
        """fast_window must be less than slow_window."""
        with pytest.raises(ValidationError):
            MovingAverageRSIStrategyConfig(fast_window=50, slow_window=20)

    def test_config_validation_rsi_levels(self):
        """RSI levels must be in valid range."""
        with pytest.raises(ValidationError):
            MovingAverageRSIStrategyConfig(rsi_oversold=80, rsi_overbought=70)

    def test_missing_columns_raises_error(self, invalid_dataframe):
        """Should raise error when required columns are missing."""
        config = MovingAverageRSIStrategyConfig()
        strategy = MovingAverageRSIStrategy(config)

        with pytest.raises(ValueError, match="Faltan columnas"):
            strategy.generate_signals(invalid_dataframe)

    def test_trend_mode_generates_continuous_signals(self, sample_ohlcv_data):
        """Trend mode should generate more signals than cross mode."""
        cross_config = MovingAverageRSIStrategyConfig(signal_mode="cross")
        trend_config = MovingAverageRSIStrategyConfig(signal_mode="trend")

        cross_strategy = MovingAverageRSIStrategy(cross_config)
        trend_strategy = MovingAverageRSIStrategy(trend_config)

        cross_signals = cross_strategy.generate_signals(sample_ohlcv_data)
        trend_signals = trend_strategy.generate_signals(sample_ohlcv_data)

        # Trend mode should have more non-zero signals
        cross_count = (cross_signals["signal"] != 0).sum()
        trend_count = (trend_signals["signal"] != 0).sum()

        assert trend_count >= cross_count


class TestSupertrendStrategy:
    """Tests for Supertrend strategy."""

    def test_generate_signals_returns_dataframe(self, sample_ohlcv_data):
        """generate_signals should return a DataFrame with signal column."""
        config = SupertrendStrategyConfig()
        strategy = SupertrendStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert "signal" in result.columns
        assert "supertrend" in result.columns
        assert "trend_dir" in result.columns

    def test_signals_are_valid_values(self, sample_ohlcv_data):
        """Signals should only be -1, 0, or 1."""
        config = SupertrendStrategyConfig()
        strategy = SupertrendStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert set(result["signal"].unique()).issubset({-1, 0, 1})

    def test_config_validation_atr_period(self):
        """atr_period must be in valid range."""
        with pytest.raises(ValidationError):
            SupertrendStrategyConfig(atr_period=0)

        with pytest.raises(ValidationError):
            SupertrendStrategyConfig(atr_period=200)

    def test_config_validation_atr_multiplier(self):
        """atr_multiplier must be in valid range."""
        with pytest.raises(ValidationError):
            SupertrendStrategyConfig(atr_multiplier=0.1)

        with pytest.raises(ValidationError):
            SupertrendStrategyConfig(atr_multiplier=15.0)

    def test_adx_filter_reduces_signals(self, sample_ohlcv_data):
        """ADX filter should reduce number of signals."""
        config_no_filter = SupertrendStrategyConfig(use_adx_filter=False)
        config_with_filter = SupertrendStrategyConfig(
            use_adx_filter=True, adx_threshold=30.0
        )

        strategy_no_filter = SupertrendStrategy(config_no_filter)
        strategy_with_filter = SupertrendStrategy(config_with_filter)

        signals_no_filter = strategy_no_filter.generate_signals(sample_ohlcv_data)
        signals_with_filter = strategy_with_filter.generate_signals(sample_ohlcv_data)

        count_no_filter = (signals_no_filter["signal"] != 0).sum()
        count_with_filter = (signals_with_filter["signal"] != 0).sum()

        # Filter should reduce or keep same number of signals
        assert count_with_filter <= count_no_filter


class TestBollingerMeanReversionStrategy:
    """Tests for Bollinger Mean Reversion strategy."""

    def test_generate_signals_returns_dataframe(self, sample_ohlcv_data):
        """generate_signals should return a DataFrame with signal column."""
        config = BollingerMeanReversionStrategyConfig()
        strategy = BollingerMeanReversionStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert "signal" in result.columns
        assert "bb_upper" in result.columns
        assert "bb_lower" in result.columns
        assert "rsi" in result.columns

    def test_signals_are_valid_values(self, sample_ohlcv_data):
        """Signals should only be -1, 0, or 1."""
        config = BollingerMeanReversionStrategyConfig()
        strategy = BollingerMeanReversionStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert set(result["signal"].unique()).issubset({-1, 0, 1})

    def test_config_validation_bb_window(self):
        """bb_window must be in valid range."""
        with pytest.raises(ValidationError):
            BollingerMeanReversionStrategyConfig(bb_window=2)

    def test_config_validation_bb_std(self):
        """bb_std must be in valid range."""
        with pytest.raises(ValidationError):
            BollingerMeanReversionStrategyConfig(bb_std=0.1)

    def test_ranging_market_generates_signals(self, ranging_data):
        """Mean reversion strategy should generate signals in ranging market."""
        config = BollingerMeanReversionStrategyConfig()
        strategy = BollingerMeanReversionStrategy(config)

        result = strategy.generate_signals(ranging_data)

        # Should have some signals in ranging market
        signal_count = (result["signal"] != 0).sum()
        assert signal_count > 0


class TestKeltnerBreakoutStrategy:
    """Tests for Keltner Breakout strategy."""

    def test_generate_signals_returns_dataframe(self, sample_ohlcv_data):
        """generate_signals should return a DataFrame with signal column."""
        config = KeltnerBreakoutStrategyConfig()
        strategy = KeltnerBreakoutStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert "signal" in result.columns
        assert "kc_upper" in result.columns
        assert "kc_lower" in result.columns

    def test_signals_are_valid_values(self, sample_ohlcv_data):
        """Signals should only be -1, 0, or 1."""
        config = KeltnerBreakoutStrategyConfig()
        strategy = KeltnerBreakoutStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert set(result["signal"].unique()).issubset({-1, 0, 1})

    def test_config_validation_kc_window(self):
        """kc_window must be in valid range."""
        with pytest.raises(ValidationError):
            KeltnerBreakoutStrategyConfig(kc_window=2)

    def test_long_only_mode(self, sample_ohlcv_data):
        """Long only mode should not generate short signals."""
        config = KeltnerBreakoutStrategyConfig(side_mode="long_only")
        strategy = KeltnerBreakoutStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert -1 not in result["signal"].values

    def test_short_only_mode(self, sample_ohlcv_data):
        """Short only mode should not generate long signals."""
        config = KeltnerBreakoutStrategyConfig(
            side_mode="short_only", allow_short=True
        )
        strategy = KeltnerBreakoutStrategy(config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert 1 not in result["signal"].values


class TestAllStrategiesParametrized:
    """Parametrized tests that run on all registered strategies."""

    @pytest.fixture
    def strategy_configs(self):
        """Get default configs for testable strategies."""
        return {
            "MA_RSI": MovingAverageRSIStrategyConfig(),
            "SUPERTREND": SupertrendStrategyConfig(),
            "BOLLINGER_MR": BollingerMeanReversionStrategyConfig(),
            "KELTNER": KeltnerBreakoutStrategyConfig(),
        }

    @pytest.mark.parametrize("strategy_type", ["MA_RSI", "SUPERTREND", "BOLLINGER_MR", "KELTNER"])
    def test_strategy_generates_valid_signals(
        self, strategy_type, strategy_configs, sample_ohlcv_data
    ):
        """All strategies should generate valid signals."""
        config = strategy_configs[strategy_type]
        strategy = create_strategy(strategy_type, config)

        result = strategy.generate_signals(sample_ohlcv_data)

        assert "signal" in result.columns
        assert set(result["signal"].unique()).issubset({-1, 0, 1})
        assert not result["signal"].isna().any()

    @pytest.mark.parametrize("strategy_type", ["MA_RSI", "SUPERTREND", "BOLLINGER_MR", "KELTNER"])
    def test_strategy_does_not_modify_input(
        self, strategy_type, strategy_configs, sample_ohlcv_data
    ):
        """Strategies should not modify the input DataFrame."""
        config = strategy_configs[strategy_type]
        strategy = create_strategy(strategy_type, config)

        original_columns = set(sample_ohlcv_data.columns)
        original_len = len(sample_ohlcv_data)

        strategy.generate_signals(sample_ohlcv_data)

        # Original DataFrame should be unchanged
        assert set(sample_ohlcv_data.columns) == original_columns
        assert len(sample_ohlcv_data) == original_len

    @pytest.mark.parametrize("strategy_type", ["MA_RSI", "SUPERTREND", "BOLLINGER_MR", "KELTNER"])
    def test_strategy_handles_empty_dataframe(self, strategy_type, strategy_configs):
        """Strategies should handle empty DataFrames gracefully."""
        config = strategy_configs[strategy_type]
        strategy = create_strategy(strategy_type, config)

        empty_df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        # Should either return empty or raise appropriate error
        try:
            result = strategy.generate_signals(empty_df)
            assert len(result) == 0
        except ValueError:
            pass  # Acceptable to raise ValueError on empty data


class TestLastSignalGeneration:
    """Tests for generate_last_signal method."""

    def test_last_signal_returns_int(self, sample_ohlcv_data):
        """generate_last_signal should return an integer."""
        config = SupertrendStrategyConfig()
        strategy = SupertrendStrategy(config)

        signal = strategy.generate_last_signal(sample_ohlcv_data)

        assert isinstance(signal, int)
        assert signal in {-1, 0, 1}

    def test_last_signal_matches_final_signal(self, sample_ohlcv_data):
        """generate_last_signal should match last signal from generate_signals."""
        config = SupertrendStrategyConfig()
        strategy = SupertrendStrategy(config)

        full_signals = strategy.generate_signals(sample_ohlcv_data)
        last_signal = strategy.generate_last_signal(sample_ohlcv_data)

        assert last_signal == int(full_signals["signal"].iloc[-1])
