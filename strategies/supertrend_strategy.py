
from dataclasses import dataclass
import pandas as pd
import numpy as np
import ta

from strategies.base import BaseStrategy, StrategyMetadata
from utils.validation import (
    ValidationError,
    validate_window_size,
    validate_multiplier,
    validate_range,
)


@dataclass
class SupertrendStrategyConfig:
    """
    Configuración para la estrategia Supertrend.

    Attributes:
        atr_period: Período para el cálculo del ATR (1-100).
        atr_multiplier: Multiplicador del ATR para las bandas (0.5-10.0).
        use_adx_filter: Si True, filtra señales usando ADX.
        adx_period: Período para el cálculo del ADX (1-100).
        adx_threshold: Umbral mínimo de ADX para confirmar tendencia (0-100).
    """
    atr_period: int = 10
    atr_multiplier: float = 3.0

    # Filtro ADX opcional
    use_adx_filter: bool = False
    adx_period: int = 14
    adx_threshold: float = 25.0

    def __post_init__(self) -> None:
        """Valida los parámetros de configuración."""
        validate_window_size(self.atr_period, "atr_period", min_window=1, max_window=100)
        validate_multiplier(self.atr_multiplier, "atr_multiplier", min_val=0.5, max_val=10.0)

        if self.use_adx_filter:
            validate_window_size(self.adx_period, "adx_period", min_window=1, max_window=100)
            validate_range(self.adx_threshold, 0, 100, "adx_threshold")


class SupertrendStrategy(BaseStrategy[SupertrendStrategyConfig]):
    """
    Estrategia basada en el indicador Supertrend.
    - Compra cuando el precio cierra por encima de la banda Supertrend (cambio a tendencia alcista).
    - Vende cuando el precio cierra por debajo de la banda Supertrend (cambio a tendencia bajista).
    - Opcionalmente filtra entradas si el ADX es bajo (mercado sin tendencia).
    """

    name: str = "SUPERTREND"

    def __init__(self, config: SupertrendStrategyConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Faltan columnas necesarias en el DataFrame: {missing}")

        c = self.config
        data = df.copy()

        # ============================
        # 1) Calcular ATR
        # ============================
        # Usamos ta.volatility.AverageTrueRange
        atr_ind = ta.volatility.AverageTrueRange(
            high=data["high"], 
            low=data["low"], 
            close=data["close"], 
            window=c.atr_period
        )
        data["atr"] = atr_ind.average_true_range()

        # ============================
        # 2) Calcular Supertrend
        # ============================
        # Implementación manual vectorizada o iterativa eficiente
        
        high = data["high"]
        low = data["low"]
        close = data["close"]
        atr = data["atr"]
        m = c.atr_multiplier

        # Basic bands
        basic_upper = (high + low) / 2 + m * atr
        basic_lower = (high + low) / 2 - m * atr

        # Inicializar columnas finales
        final_upper = pd.Series(index=data.index, dtype='float64')
        final_lower = pd.Series(index=data.index, dtype='float64')
        supertrend = pd.Series(index=data.index, dtype='float64')
        
        # 1: Uptrend, -1: Downtrend
        trend = pd.Series(0, index=data.index, dtype='int')

        # Cálculo iterativo (Supertrend es recursivo)
        # Se puede optimizar con Numba, pero para backtest en Python puro:
        
        # Valores iniciales
        final_upper.iloc[0] = basic_upper.iloc[0]
        final_lower.iloc[0] = basic_lower.iloc[0]
        
        # Iteramos desde la segunda vela
        for i in range(1, len(data)):
            # --- FINAL UPPER BAND ---
            if basic_upper.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
                final_upper.iloc[i] = basic_upper.iloc[i]
            else:
                final_upper.iloc[i] = final_upper.iloc[i-1]

            # --- FINAL LOWER BAND ---
            if basic_lower.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
                final_lower.iloc[i] = basic_lower.iloc[i]
            else:
                final_lower.iloc[i] = final_lower.iloc[i-1]

            # --- TREND ---
            # Si la tendencia previa era alcista (1)
            if trend.iloc[i-1] == 1:
                if close.iloc[i] < final_lower.iloc[i]:
                    trend.iloc[i] = -1 # Cambio a bajista
                else:
                    trend.iloc[i] = 1 # Mantiene alcista
            
            # Si la tendencia previa era bajista (-1) o neutra (0)
            else:
                if close.iloc[i] > final_upper.iloc[i]:
                    trend.iloc[i] = 1 # Cambio a alcista
                else:
                    trend.iloc[i] = -1 # Mantiene bajista

            # --- SUPERTREND VALUE ---
            if trend.iloc[i] == 1:
                supertrend.iloc[i] = final_lower.iloc[i]
            else:
                supertrend.iloc[i] = final_upper.iloc[i]

        data["supertrend"] = supertrend
        data["trend_dir"] = trend

        # ============================
        # 3) Generar Señales
        # ============================
        data["signal"] = 0
        
        # Cruce de precio con Supertrend
        # Cambio de tendencia de -1 a 1 => Compra
        # Cambio de tendencia de 1 a -1 => Venta
        
        prev_trend = data["trend_dir"].shift(1)
        
        # Buy: Trend pasa a 1
        data.loc[(prev_trend == -1) & (data["trend_dir"] == 1), "signal"] = 1
        
        # Sell: Trend pasa a -1
        data.loc[(prev_trend == 1) & (data["trend_dir"] == -1), "signal"] = -1

        # ============================
        # 4) Filtro ADX (Opcional)
        # ============================
        if c.use_adx_filter:
            adx_ind = ta.trend.ADXIndicator(high=data["high"], low=data["low"], close=data["close"], window=c.adx_period)
            data["adx"] = adx_ind.adx()
            
            # Si ADX < threshold, anulamos señales (mercado lateral)
            weak_trend = data["adx"] < c.adx_threshold
            data.loc[weak_trend, "signal"] = 0

        return data
