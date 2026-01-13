# utils/validation.py
"""
Módulo de validación centralizada para el bot de trading.

Proporciona:
- Validación de DataFrames OHLCV
- Validación de parámetros de configuración
- Decoradores para validación automática
- Funciones de utilidad para validar rangos y tipos
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from functools import wraps
from typing import Any, Callable, Optional, Set, TypeVar

import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


# Columnas requeridas para datos OHLCV
REQUIRED_OHLCV_COLUMNS: Set[str] = {"timestamp", "open", "high", "low", "close", "volume"}


class ValidationError(Exception):
    """Excepción para errores de validación."""

    pass


def validate_ohlcv_dataframe(
    df: pd.DataFrame,
    require_volume: bool = True,
    check_ohlc_consistency: bool = True,
    check_for_nans: bool = True,
    min_rows: int = 1,
) -> None:
    """
    Valida que un DataFrame contenga datos OHLCV válidos.

    Args:
        df: DataFrame a validar.
        require_volume: Si True, valida que exista y sea válido el volumen.
        check_ohlc_consistency: Si True, verifica que high >= low y open/close estén dentro del rango.
        check_for_nans: Si True, verifica que no haya NaN en columnas críticas.
        min_rows: Número mínimo de filas requeridas.

    Raises:
        ValidationError: Si el DataFrame no pasa las validaciones.
    """
    if df is None:
        raise ValidationError("DataFrame es None")

    if df.empty:
        raise ValidationError("DataFrame está vacío")

    if len(df) < min_rows:
        raise ValidationError(
            f"DataFrame tiene {len(df)} filas, se requieren al menos {min_rows}"
        )

    # Verificar columnas requeridas
    required_cols = REQUIRED_OHLCV_COLUMNS.copy()
    if not require_volume:
        required_cols.discard("volume")

    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValidationError(f"Columnas faltantes en DataFrame: {missing_cols}")

    # Verificar NaN en columnas OHLC
    if check_for_nans:
        ohlc_cols = ["open", "high", "low", "close"]
        for col in ohlc_cols:
            if df[col].isna().any():
                nan_count = df[col].isna().sum()
                raise ValidationError(
                    f"Columna '{col}' contiene {nan_count} valores NaN"
                )

    # Verificar consistencia OHLC
    if check_ohlc_consistency:
        # High debe ser >= Low
        invalid_hl = df["high"] < df["low"]
        if invalid_hl.any():
            count = invalid_hl.sum()
            raise ValidationError(
                f"Datos OHLC inconsistentes: {count} filas donde high < low"
            )

        # High debe ser >= Open y Close
        invalid_high = (df["high"] < df["open"]) | (df["high"] < df["close"])
        if invalid_high.any():
            count = invalid_high.sum()
            raise ValidationError(
                f"Datos OHLC inconsistentes: {count} filas donde high < open o high < close"
            )

        # Low debe ser <= Open y Close
        invalid_low = (df["low"] > df["open"]) | (df["low"] > df["close"])
        if invalid_low.any():
            count = invalid_low.sum()
            raise ValidationError(
                f"Datos OHLC inconsistentes: {count} filas donde low > open o low > close"
            )

    # Verificar volumen
    if require_volume:
        if df["volume"].isna().any():
            nan_count = df["volume"].isna().sum()
            raise ValidationError(
                f"Columna 'volume' contiene {nan_count} valores NaN"
            )

        if (df["volume"] < 0).any():
            count = (df["volume"] < 0).sum()
            raise ValidationError(
                f"Volumen negativo detectado en {count} filas"
            )

    logger.debug(f"DataFrame OHLCV validado correctamente: {len(df)} filas")


def validate_range(
    value: float | int,
    min_val: Optional[float | int] = None,
    max_val: Optional[float | int] = None,
    param_name: str = "value",
    exclusive_min: bool = False,
    exclusive_max: bool = False,
) -> None:
    """
    Valida que un valor esté dentro de un rango especificado.

    Args:
        value: Valor a validar.
        min_val: Valor mínimo permitido (inclusive por defecto).
        max_val: Valor máximo permitido (inclusive por defecto).
        param_name: Nombre del parámetro para mensajes de error.
        exclusive_min: Si True, el mínimo es exclusivo.
        exclusive_max: Si True, el máximo es exclusivo.

    Raises:
        ValidationError: Si el valor está fuera del rango.
    """
    if min_val is not None:
        if exclusive_min:
            if value <= min_val:
                raise ValidationError(
                    f"{param_name} debe ser mayor que {min_val}, valor actual: {value}"
                )
        else:
            if value < min_val:
                raise ValidationError(
                    f"{param_name} debe ser >= {min_val}, valor actual: {value}"
                )

    if max_val is not None:
        if exclusive_max:
            if value >= max_val:
                raise ValidationError(
                    f"{param_name} debe ser menor que {max_val}, valor actual: {value}"
                )
        else:
            if value > max_val:
                raise ValidationError(
                    f"{param_name} debe ser <= {max_val}, valor actual: {value}"
                )


def validate_positive(value: float | int, param_name: str = "value") -> None:
    """
    Valida que un valor sea positivo (> 0).

    Args:
        value: Valor a validar.
        param_name: Nombre del parámetro para mensajes de error.

    Raises:
        ValidationError: Si el valor no es positivo.
    """
    if value <= 0:
        raise ValidationError(f"{param_name} debe ser positivo, valor actual: {value}")


def validate_non_negative(value: float | int, param_name: str = "value") -> None:
    """
    Valida que un valor sea no negativo (>= 0).

    Args:
        value: Valor a validar.
        param_name: Nombre del parámetro para mensajes de error.

    Raises:
        ValidationError: Si el valor es negativo.
    """
    if value < 0:
        raise ValidationError(
            f"{param_name} debe ser >= 0, valor actual: {value}"
        )


def validate_percentage(
    value: float,
    param_name: str = "value",
    allow_zero: bool = True,
    allow_hundred: bool = True,
) -> None:
    """
    Valida que un valor sea un porcentaje válido (0-100).

    Args:
        value: Valor a validar.
        param_name: Nombre del parámetro para mensajes de error.
        allow_zero: Si True, permite el valor 0.
        allow_hundred: Si True, permite el valor 100.

    Raises:
        ValidationError: Si el valor no es un porcentaje válido.
    """
    min_val = 0 if allow_zero else 0 + 1e-10
    max_val = 100 if allow_hundred else 100 - 1e-10

    if value < min_val or value > max_val:
        raise ValidationError(
            f"{param_name} debe estar entre 0 y 100, valor actual: {value}"
        )


def validate_ratio(
    value: float,
    param_name: str = "value",
    min_val: float = 0.0,
    max_val: float = 1.0,
) -> None:
    """
    Valida que un valor sea un ratio válido (típicamente 0-1).

    Args:
        value: Valor a validar.
        param_name: Nombre del parámetro para mensajes de error.
        min_val: Valor mínimo permitido.
        max_val: Valor máximo permitido.

    Raises:
        ValidationError: Si el valor no es un ratio válido.
    """
    validate_range(value, min_val, max_val, param_name)


T = TypeVar("T")


def validate_dataclass_config(config: T) -> T:
    """
    Valida una configuración dataclass usando las validaciones definidas en __post_init__.

    Si el dataclass no tiene __post_init__, simplemente devuelve la configuración.

    Args:
        config: Objeto dataclass a validar.

    Returns:
        El mismo objeto si la validación pasa.

    Raises:
        ValidationError: Si la configuración no es válida.
    """
    if not is_dataclass(config):
        raise ValidationError(f"El objeto {type(config).__name__} no es un dataclass")

    # El __post_init__ ya se ejecutó durante la creación
    # Esta función es para re-validar si es necesario
    return config


# Decorador para validar DataFrame de entrada
def validate_input_df(
    require_volume: bool = True,
    min_rows: int = 1,
) -> Callable:
    """
    Decorador que valida el DataFrame de entrada de una función.

    Asume que el primer argumento (o 'df' en kwargs) es el DataFrame a validar.

    Args:
        require_volume: Si True, valida que exista columna de volumen.
        min_rows: Número mínimo de filas requeridas.

    Returns:
        Función decorada con validación de entrada.

    Example:
        @validate_input_df(min_rows=100)
        def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Buscar el DataFrame en args o kwargs
            df = None

            # Si es un método, el primer arg es self, el segundo es df
            if len(args) >= 2 and isinstance(args[1], pd.DataFrame):
                df = args[1]
            elif len(args) >= 1 and isinstance(args[0], pd.DataFrame):
                df = args[0]
            elif "df" in kwargs:
                df = kwargs["df"]

            if df is not None:
                validate_ohlcv_dataframe(
                    df,
                    require_volume=require_volume,
                    min_rows=min_rows,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


# Funciones de validación específicas para trading
def validate_window_size(
    window: int,
    param_name: str = "window",
    min_window: int = 1,
    max_window: int = 1000,
) -> None:
    """
    Valida el tamaño de una ventana para indicadores técnicos.

    Args:
        window: Tamaño de ventana a validar.
        param_name: Nombre del parámetro para mensajes de error.
        min_window: Tamaño mínimo de ventana.
        max_window: Tamaño máximo de ventana.

    Raises:
        ValidationError: Si el tamaño de ventana no es válido.
    """
    if not isinstance(window, int):
        raise ValidationError(
            f"{param_name} debe ser un entero, tipo actual: {type(window).__name__}"
        )
    validate_range(window, min_window, max_window, param_name)


def validate_multiplier(
    multiplier: float,
    param_name: str = "multiplier",
    min_val: float = 0.1,
    max_val: float = 10.0,
) -> None:
    """
    Valida un multiplicador (típicamente para ATR, desviación estándar, etc.).

    Args:
        multiplier: Multiplicador a validar.
        param_name: Nombre del parámetro para mensajes de error.
        min_val: Valor mínimo permitido.
        max_val: Valor máximo permitido.

    Raises:
        ValidationError: Si el multiplicador no es válido.
    """
    validate_range(multiplier, min_val, max_val, param_name)


def validate_rsi_levels(
    oversold: float,
    overbought: float,
) -> None:
    """
    Valida los niveles de RSI para sobrecompra y sobreventa.

    Args:
        oversold: Nivel de sobreventa (típicamente 20-40).
        overbought: Nivel de sobrecompra (típicamente 60-80).

    Raises:
        ValidationError: Si los niveles no son válidos.
    """
    validate_range(oversold, 0, 100, "rsi_oversold")
    validate_range(overbought, 0, 100, "rsi_overbought")

    if oversold >= overbought:
        raise ValidationError(
            f"rsi_oversold ({oversold}) debe ser menor que rsi_overbought ({overbought})"
        )


def validate_ma_windows(
    fast_window: int,
    slow_window: int,
) -> None:
    """
    Valida ventanas de medias móviles (fast debe ser menor que slow).

    Args:
        fast_window: Ventana de MA rápida.
        slow_window: Ventana de MA lenta.

    Raises:
        ValidationError: Si las ventanas no son válidas.
    """
    validate_window_size(fast_window, "fast_window")
    validate_window_size(slow_window, "slow_window")

    if fast_window >= slow_window:
        raise ValidationError(
            f"fast_window ({fast_window}) debe ser menor que slow_window ({slow_window})"
        )


def validate_price(price: float, param_name: str = "price") -> None:
    """
    Valida que un precio sea válido (positivo y finito).

    Args:
        price: Precio a validar.
        param_name: Nombre del parámetro para mensajes de error.

    Raises:
        ValidationError: Si el precio no es válido.
    """
    if not np.isfinite(price):
        raise ValidationError(f"{param_name} debe ser un número finito: {price}")
    validate_positive(price, param_name)


def validate_capital(capital: float, param_name: str = "capital") -> None:
    """
    Valida que el capital sea válido.

    Args:
        capital: Capital a validar.
        param_name: Nombre del parámetro para mensajes de error.

    Raises:
        ValidationError: Si el capital no es válido.
    """
    validate_positive(capital, param_name)
