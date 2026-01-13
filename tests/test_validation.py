# tests/test_validation.py
"""
Tests for the validation module.

Tests include:
- DataFrame validation
- Range validation
- Parameter-specific validators
- Decorator functionality
"""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from utils.validation import (
    ValidationError,
    validate_ohlcv_dataframe,
    validate_range,
    validate_positive,
    validate_non_negative,
    validate_percentage,
    validate_ratio,
    validate_window_size,
    validate_multiplier,
    validate_rsi_levels,
    validate_ma_windows,
    validate_price,
    validate_capital,
    validate_input_df,
    REQUIRED_OHLCV_COLUMNS,
)


class TestValidateOHLCVDataFrame:
    """Tests for OHLCV DataFrame validation."""

    def test_valid_dataframe_passes(self, sample_ohlcv_data):
        """Valid OHLCV DataFrame should pass validation."""
        # Should not raise
        validate_ohlcv_dataframe(sample_ohlcv_data)

    def test_none_dataframe_raises_error(self):
        """None DataFrame should raise ValidationError."""
        with pytest.raises(ValidationError, match="None"):
            validate_ohlcv_dataframe(None)

    def test_empty_dataframe_raises_error(self):
        """Empty DataFrame should raise ValidationError."""
        empty_df = pd.DataFrame(columns=list(REQUIRED_OHLCV_COLUMNS))
        with pytest.raises(ValidationError, match="vacío"):
            validate_ohlcv_dataframe(empty_df)

    def test_missing_columns_raises_error(self, invalid_dataframe):
        """DataFrame missing required columns should raise error."""
        with pytest.raises(ValidationError, match="Columnas faltantes"):
            validate_ohlcv_dataframe(invalid_dataframe)

    def test_nan_values_raises_error(self, dataframe_with_nans):
        """DataFrame with NaN in OHLC columns should raise error."""
        with pytest.raises(ValidationError, match="NaN"):
            validate_ohlcv_dataframe(dataframe_with_nans)

    def test_invalid_ohlc_consistency(self):
        """DataFrame where high < low should raise error."""
        df = pd.DataFrame({
            "timestamp": [datetime.now()],
            "open": [100.0],
            "high": [99.0],   # Invalid: lower than low
            "low": [101.0],   # Invalid: higher than high
            "close": [100.0],
            "volume": [1000.0],
        })

        with pytest.raises(ValidationError, match="high < low"):
            validate_ohlcv_dataframe(df)

    def test_negative_volume_raises_error(self):
        """DataFrame with negative volume should raise error."""
        df = pd.DataFrame({
            "timestamp": [datetime.now()],
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.0],
            "volume": [-1000.0],  # Invalid
        })

        with pytest.raises(ValidationError, match="negativo"):
            validate_ohlcv_dataframe(df)

    def test_min_rows_validation(self, sample_ohlcv_data):
        """DataFrame with fewer rows than required should raise error."""
        small_df = sample_ohlcv_data.head(5)

        with pytest.raises(ValidationError, match="filas"):
            validate_ohlcv_dataframe(small_df, min_rows=100)

    def test_skip_volume_validation(self):
        """Should skip volume validation when require_volume=False."""
        df = pd.DataFrame({
            "timestamp": [datetime.now()],
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.0],
            "volume": [np.nan],  # NaN volume
        })

        # Should not raise when volume not required
        validate_ohlcv_dataframe(df, require_volume=False, check_for_nans=False)


class TestValidateRange:
    """Tests for range validation."""

    def test_valid_value_in_range(self):
        """Value within range should pass."""
        validate_range(5, min_val=0, max_val=10, param_name="test")

    def test_value_below_min_raises_error(self):
        """Value below minimum should raise error."""
        with pytest.raises(ValidationError, match=">="):
            validate_range(-1, min_val=0, max_val=10, param_name="test")

    def test_value_above_max_raises_error(self):
        """Value above maximum should raise error."""
        with pytest.raises(ValidationError, match="<="):
            validate_range(15, min_val=0, max_val=10, param_name="test")

    def test_exclusive_min(self):
        """Exclusive min should reject equal values."""
        with pytest.raises(ValidationError, match="mayor que"):
            validate_range(0, min_val=0, exclusive_min=True, param_name="test")

    def test_exclusive_max(self):
        """Exclusive max should reject equal values."""
        with pytest.raises(ValidationError, match="menor que"):
            validate_range(10, max_val=10, exclusive_max=True, param_name="test")


class TestValidatePositive:
    """Tests for positive validation."""

    def test_positive_value_passes(self):
        """Positive value should pass."""
        validate_positive(1, param_name="test")
        validate_positive(0.001, param_name="test")

    def test_zero_raises_error(self):
        """Zero should raise error."""
        with pytest.raises(ValidationError, match="positivo"):
            validate_positive(0, param_name="test")

    def test_negative_raises_error(self):
        """Negative value should raise error."""
        with pytest.raises(ValidationError, match="positivo"):
            validate_positive(-1, param_name="test")


class TestValidateNonNegative:
    """Tests for non-negative validation."""

    def test_positive_value_passes(self):
        """Positive value should pass."""
        validate_non_negative(1, param_name="test")

    def test_zero_passes(self):
        """Zero should pass."""
        validate_non_negative(0, param_name="test")

    def test_negative_raises_error(self):
        """Negative value should raise error."""
        with pytest.raises(ValidationError, match=">="):
            validate_non_negative(-1, param_name="test")


class TestValidatePercentage:
    """Tests for percentage validation."""

    def test_valid_percentage_passes(self):
        """Valid percentage (0-100) should pass."""
        validate_percentage(50, param_name="test")
        validate_percentage(0, param_name="test")
        validate_percentage(100, param_name="test")

    def test_negative_percentage_raises_error(self):
        """Negative percentage should raise error."""
        with pytest.raises(ValidationError):
            validate_percentage(-1, param_name="test")

    def test_over_100_raises_error(self):
        """Percentage > 100 should raise error."""
        with pytest.raises(ValidationError):
            validate_percentage(101, param_name="test")


class TestValidateRatio:
    """Tests for ratio validation."""

    def test_valid_ratio_passes(self):
        """Valid ratio (0-1) should pass."""
        validate_ratio(0.5, param_name="test")
        validate_ratio(0, param_name="test")
        validate_ratio(1, param_name="test")

    def test_negative_ratio_raises_error(self):
        """Negative ratio should raise error."""
        with pytest.raises(ValidationError):
            validate_ratio(-0.1, param_name="test")

    def test_over_1_raises_error(self):
        """Ratio > 1 should raise error."""
        with pytest.raises(ValidationError):
            validate_ratio(1.1, param_name="test")


class TestValidateWindowSize:
    """Tests for window size validation."""

    def test_valid_window_passes(self):
        """Valid window size should pass."""
        validate_window_size(14, param_name="window")
        validate_window_size(1, param_name="window")
        validate_window_size(1000, param_name="window")

    def test_zero_window_raises_error(self):
        """Zero window should raise error."""
        with pytest.raises(ValidationError):
            validate_window_size(0, param_name="window")

    def test_negative_window_raises_error(self):
        """Negative window should raise error."""
        with pytest.raises(ValidationError):
            validate_window_size(-1, param_name="window")

    def test_non_integer_raises_error(self):
        """Non-integer window should raise error."""
        with pytest.raises(ValidationError, match="entero"):
            validate_window_size(14.5, param_name="window")


class TestValidateMultiplier:
    """Tests for multiplier validation."""

    def test_valid_multiplier_passes(self):
        """Valid multiplier should pass."""
        validate_multiplier(2.0, param_name="mult")
        validate_multiplier(0.1, param_name="mult")
        validate_multiplier(10.0, param_name="mult")

    def test_too_small_multiplier_raises_error(self):
        """Multiplier below minimum should raise error."""
        with pytest.raises(ValidationError):
            validate_multiplier(0.05, param_name="mult")  # Default min is 0.1

    def test_too_large_multiplier_raises_error(self):
        """Multiplier above maximum should raise error."""
        with pytest.raises(ValidationError):
            validate_multiplier(15.0, param_name="mult")  # Default max is 10.0


class TestValidateRSILevels:
    """Tests for RSI level validation."""

    def test_valid_rsi_levels_pass(self):
        """Valid RSI levels should pass."""
        validate_rsi_levels(oversold=30.0, overbought=70.0)
        validate_rsi_levels(oversold=20.0, overbought=80.0)

    def test_oversold_greater_than_overbought_raises_error(self):
        """oversold >= overbought should raise error."""
        with pytest.raises(ValidationError, match="menor que"):
            validate_rsi_levels(oversold=70.0, overbought=30.0)

    def test_equal_levels_raises_error(self):
        """Equal levels should raise error."""
        with pytest.raises(ValidationError, match="menor que"):
            validate_rsi_levels(oversold=50.0, overbought=50.0)

    def test_out_of_range_levels_raise_error(self):
        """Levels outside 0-100 should raise error."""
        with pytest.raises(ValidationError):
            validate_rsi_levels(oversold=-10.0, overbought=70.0)

        with pytest.raises(ValidationError):
            validate_rsi_levels(oversold=30.0, overbought=110.0)


class TestValidateMAWindows:
    """Tests for moving average window validation."""

    def test_valid_ma_windows_pass(self):
        """Valid MA windows (fast < slow) should pass."""
        validate_ma_windows(fast_window=10, slow_window=50)
        validate_ma_windows(fast_window=5, slow_window=200)

    def test_fast_greater_than_slow_raises_error(self):
        """fast_window >= slow_window should raise error."""
        with pytest.raises(ValidationError, match="menor que"):
            validate_ma_windows(fast_window=50, slow_window=10)

    def test_equal_windows_raises_error(self):
        """Equal windows should raise error."""
        with pytest.raises(ValidationError, match="menor que"):
            validate_ma_windows(fast_window=20, slow_window=20)


class TestValidatePrice:
    """Tests for price validation."""

    def test_valid_price_passes(self):
        """Valid positive price should pass."""
        validate_price(100.0, param_name="price")
        validate_price(0.001, param_name="price")

    def test_zero_price_raises_error(self):
        """Zero price should raise error."""
        with pytest.raises(ValidationError, match="positivo"):
            validate_price(0.0, param_name="price")

    def test_negative_price_raises_error(self):
        """Negative price should raise error."""
        with pytest.raises(ValidationError, match="positivo"):
            validate_price(-100.0, param_name="price")

    def test_infinite_price_raises_error(self):
        """Infinite price should raise error."""
        with pytest.raises(ValidationError, match="finito"):
            validate_price(float("inf"), param_name="price")

    def test_nan_price_raises_error(self):
        """NaN price should raise error."""
        with pytest.raises(ValidationError, match="finito"):
            validate_price(float("nan"), param_name="price")


class TestValidateCapital:
    """Tests for capital validation."""

    def test_valid_capital_passes(self):
        """Valid positive capital should pass."""
        validate_capital(10000.0, param_name="capital")
        validate_capital(1.0, param_name="capital")

    def test_zero_capital_raises_error(self):
        """Zero capital should raise error."""
        with pytest.raises(ValidationError, match="positivo"):
            validate_capital(0.0, param_name="capital")


class TestValidateInputDfDecorator:
    """Tests for validate_input_df decorator."""

    def test_decorator_validates_valid_df(self, sample_ohlcv_data):
        """Decorator should allow valid DataFrame through."""

        @validate_input_df(min_rows=1)
        def process_data(df: pd.DataFrame) -> pd.DataFrame:
            return df

        result = process_data(sample_ohlcv_data)
        assert len(result) == len(sample_ohlcv_data)

    def test_decorator_rejects_invalid_df(self, invalid_dataframe):
        """Decorator should reject invalid DataFrame."""

        @validate_input_df()
        def process_data(df: pd.DataFrame) -> pd.DataFrame:
            return df

        with pytest.raises(ValidationError, match="Columnas faltantes"):
            process_data(invalid_dataframe)

    def test_decorator_checks_min_rows(self, sample_ohlcv_data):
        """Decorator should check minimum rows."""

        @validate_input_df(min_rows=1000)  # More than sample data
        def process_data(df: pd.DataFrame) -> pd.DataFrame:
            return df

        with pytest.raises(ValidationError, match="filas"):
            process_data(sample_ohlcv_data)
