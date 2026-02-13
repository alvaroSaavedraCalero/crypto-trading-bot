import yfinance as yf
import pandas as pd
from typing import Optional

def get_yfinance_data(symbol: str, timeframe: str = "1d", limit: int = 1000, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Descarga datos de yfinance.
    """
    try:
        # Convertir timeframe format (ej 15m -> 15m)
        # yfinance soporta 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        
        # Mapping simple si es necesario
        interval = timeframe
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return None
            
        # Renombrar columnas a minúsculas
        df.columns = [c.lower() for c in df.columns]
        
        # Convertir index a columna timestamp para compatibilidad con estrategias
        df.index.name = "timestamp"
        df = df.reset_index()

        # Filtrar columnas requeridas
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        if not all(c in df.columns for c in required):
            return None

        return df[required]
        
    except Exception as e:
        print(f"Error descargando datos para {symbol}: {e}")
        return None
