# strategies/ma_rsi_strategy.py

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import ta

from strategies.base import BaseStrategy
from .base import BaseStrategy, StrategyMetadata
from utils.validation import (
    ValidationError,
    validate_window_size,
    validate_rsi_levels,
    validate_ma_windows,
)


SignalMode = Literal["cross", "trend"]


@dataclass
class MovingAverageRSIStrategyConfig:
    """
    Configuración para la estrategia de Media Móvil con RSI.

    Attributes:
        fast_window: Período de la media móvil rápida (1-500).
        slow_window: Período de la media móvil lenta (debe ser > fast_window).
        rsi_window: Período para el cálculo del RSI (1-100).
        rsi_overbought: Nivel de sobrecompra del RSI (50-100).
        rsi_oversold: Nivel de sobreventa del RSI (0-50).
        use_rsi_filter: Si True, filtra señales usando RSI.
        signal_mode: Modo de señal - "cross" para cruces, "trend" para tendencia continua.
        use_trend_filter: Si True, filtra señales usando MA de tendencia.
        trend_ma_window: Período de la MA de tendencia larga.
    """
    fast_window: int = 10
    slow_window: int = 20
    rsi_window: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    use_rsi_filter: bool = False
    signal_mode: SignalMode = "cross"  # "cross" o "trend"

    # NUEVOS campos de filtro de tendencia
    use_trend_filter: bool = False
    trend_ma_window: int = 200  # MA larga para definir tendencia

    def __post_init__(self) -> None:
        """Valida los parámetros de configuración."""
        # Validar ventanas de MA
        validate_ma_windows(self.fast_window, self.slow_window)

        # Validar ventana RSI
        validate_window_size(self.rsi_window, "rsi_window", min_window=2, max_window=100)

        # Validar niveles RSI
        validate_rsi_levels(self.rsi_oversold, self.rsi_overbought)

        # Validar ventana de tendencia
        if self.use_trend_filter:
            validate_window_size(
                self.trend_ma_window, "trend_ma_window",
                min_window=self.slow_window + 1, max_window=1000
            )

        # Validar signal_mode
        if self.signal_mode not in ("cross", "trend"):
            raise ValidationError(
                f"signal_mode debe ser 'cross' o 'trend', valor actual: {self.signal_mode}"
            )


class MovingAverageRSIStrategy(BaseStrategy[MovingAverageRSIStrategyConfig]):
    """
    Estrategia basada en:
    - Cruce de medias móviles (fast/slow)
    - Opcional filtro RSI
    - Opcional filtro de tendencia con MA larga
    """

    name: str = "MA_RSI"

    def __init__(self, config: MovingAverageRSIStrategyConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Faltan columnas necesarias en el DataFrame: {missing}")

        c = self.config
        data = df.copy()

        # ============================
        # 1) Medias móviles
        # ============================
        data["fast_ma"] = data["close"].rolling(window=c.fast_window, min_periods=c.fast_window).mean()
        data["slow_ma"] = data["close"].rolling(window=c.slow_window, min_periods=c.slow_window).mean()

        # ============================
        # 2) Señal básica (sin filtros)
        # ============================
        data["signal"] = 0

        if c.signal_mode == "trend":
            # Señal continua según relación fast/slow
            data.loc[data["fast_ma"] > data["slow_ma"], "signal"] = 1
            data.loc[data["fast_ma"] < data["slow_ma"], "signal"] = -1

        elif c.signal_mode == "cross":
            # Señal solo cuando hay cruce
            prev_fast = data["fast_ma"].shift(1)
            prev_slow = data["slow_ma"].shift(1)

            cross_up = (prev_fast <= prev_slow) & (data["fast_ma"] > data["slow_ma"])
            cross_down = (prev_fast >= prev_slow) & (data["fast_ma"] < data["slow_ma"])

            data.loc[cross_up, "signal"] = 1
            data.loc[cross_down, "signal"] = -1

        else:
            raise ValueError(f"signal_mode no soportado: {c.signal_mode}")

        # ============================
        # 3) Filtro RSI opcional
        # ============================
        if c.use_rsi_filter:
            rsi_ind = ta.momentum.RSIIndicator(close=data["close"], window=c.rsi_window)
            data["rsi"] = rsi_ind.rsi()

            # Ejemplo de lógica:
            # - Para largos: evitamos sobrecompra extrema
            # - Para cortos: evitamos sobreventa extrema
            long_mask = data["signal"] == 1
            short_mask = data["signal"] == -1

            data.loc[long_mask & (data["rsi"] > c.rsi_overbought), "signal"] = 0
            data.loc[short_mask & (data["rsi"] < c.rsi_oversold), "signal"] = 0

        # ============================
        # 4) Filtro de tendencia opcional
        # ============================
        if c.use_trend_filter:
            data["trend_ma"] = data["close"].rolling(
                window=c.trend_ma_window,
                min_periods=c.trend_ma_window,
            ).mean()

            # Solo consideramos señales donde la MA de tendencia no es NaN
            valid_trend = data["trend_ma"].notna()

            # Definimos tendencia: arriba si close > trend_ma, abajo si close < trend_ma
            up_trend = valid_trend & (data["close"] > data["trend_ma"])
            down_trend = valid_trend & (data["close"] < data["trend_ma"])

            # Anulamos largos en tendencia bajista
            data.loc[(data["signal"] == 1) & ~up_trend, "signal"] = 0

            # Anulamos cortos en tendencia alcista
            data.loc[(data["signal"] == -1) & ~down_trend, "signal"] = 0

        # Opcional: poner a 0 las señales donde no haya fast/slow MA válidas
        valid_ma = data["fast_ma"].notna() & data["slow_ma"].notna()
        data.loc[~valid_ma, "signal"] = 0

        return data