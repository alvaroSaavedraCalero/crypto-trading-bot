
from dataclasses import dataclass
import pandas as pd
import ta

from strategies.base import BaseStrategy, StrategyMetadata


@dataclass
class BollingerMeanReversionStrategyConfig:
    bb_window: int = 20
    bb_std: float = 2.0
    
    rsi_window: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0


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
