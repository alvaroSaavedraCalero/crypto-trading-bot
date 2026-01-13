
from dataclasses import dataclass
import pandas as pd
import ta

from strategies.base import BaseStrategy, StrategyMetadata
from utils.validation import (
    validate_window_size,
    validate_multiplier,
    validate_rsi_levels,
)


@dataclass
class BollingerMeanReversionStrategyConfig:
    """
    Configuración para la estrategia de Reversión a la Media con Bollinger.

    Attributes:
        bb_window: Período para las Bandas de Bollinger (5-200).
        bb_std: Número de desviaciones estándar para las bandas (0.5-5.0).
        rsi_window: Período para el cálculo del RSI (2-100).
        rsi_oversold: Nivel de sobreventa del RSI (0-50).
        rsi_overbought: Nivel de sobrecompra del RSI (50-100).
    """
    bb_window: int = 20
    bb_std: float = 2.0

    rsi_window: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    def __post_init__(self) -> None:
        """Valida los parámetros de configuración."""
        validate_window_size(self.bb_window, "bb_window", min_window=5, max_window=200)
        validate_multiplier(self.bb_std, "bb_std", min_val=0.5, max_val=5.0)
        validate_window_size(self.rsi_window, "rsi_window", min_window=2, max_window=100)
        validate_rsi_levels(self.rsi_oversold, self.rsi_overbought)


class BollingerMeanReversionStrategy(BaseStrategy[BollingerMeanReversionStrategyConfig]):
    """
    Estrategia de Reversión a la Media con Bandas de Bollinger y RSI.
    - Compra cuando el precio toca la banda inferior Y el RSI está en sobreventa.
    - Vende cuando el precio toca la banda superior Y el RSI está en sobrecompra.
    - Ideal para mercados laterales (ranging).
    """

    name: str = "BOLLINGER_MR"

    def __init__(self, config: BollingerMeanReversionStrategyConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Faltan columnas necesarias en el DataFrame: {missing}")

        c = self.config
        data = df.copy()

        # ============================
        # 1) Calcular Bollinger Bands
        # ============================
        bb_ind = ta.volatility.BollingerBands(
            close=data["close"], 
            window=c.bb_window, 
            window_dev=c.bb_std
        )
        data["bb_upper"] = bb_ind.bollinger_hband()
        data["bb_lower"] = bb_ind.bollinger_lband()
        
        # ============================
        # 2) Calcular RSI
        # ============================
        rsi_ind = ta.momentum.RSIIndicator(close=data["close"], window=c.rsi_window)
        data["rsi"] = rsi_ind.rsi()

        # ============================
        # 3) Generar Señales
        # ============================
        data["signal"] = 0
        
        # Long: Close < Lower Band AND RSI < Oversold
        long_cond = (data["close"] < data["bb_lower"]) & (data["rsi"] < c.rsi_oversold)
        data.loc[long_cond, "signal"] = 1
        
        # Short: Close > Upper Band AND RSI > Overbought
        short_cond = (data["close"] > data["bb_upper"]) & (data["rsi"] > c.rsi_overbought)
        data.loc[short_cond, "signal"] = -1

        return data
