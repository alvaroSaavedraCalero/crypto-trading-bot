
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

        # Validate minimum data length
        if len(data) < c.atr_period:
            data["signal"] = 0
            return data

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
        hl2 = (high + low) / 2
        basic_upper = hl2 + m * atr
        basic_lower = hl2 - m * atr

        # Use numpy arrays for fast iteration (Supertrend is inherently recursive)
        n = len(data)
        bu = basic_upper.values
        bl = basic_lower.values
        cl = close.values

        fu = np.empty(n, dtype=np.float64)
        fl = np.empty(n, dtype=np.float64)
        tr = np.empty(n, dtype=np.int64)
        st = np.empty(n, dtype=np.float64)

        fu[0] = bu[0]
        fl[0] = bl[0]
        tr[0] = 0
        st[0] = np.nan

        for i in range(1, n):
            # Final upper band
            fu[i] = bu[i] if (bu[i] < fu[i - 1] or cl[i - 1] > fu[i - 1]) else fu[i - 1]

            # Final lower band
            fl[i] = bl[i] if (bl[i] > fl[i - 1] or cl[i - 1] < fl[i - 1]) else fl[i - 1]

            # Trend direction
            if tr[i - 1] == 1:
                tr[i] = -1 if cl[i] < fl[i] else 1
            else:
                tr[i] = 1 if cl[i] > fu[i] else -1

            # Supertrend value
            st[i] = fl[i] if tr[i] == 1 else fu[i]

        data["supertrend"] = st
        data["trend_dir"] = tr

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
