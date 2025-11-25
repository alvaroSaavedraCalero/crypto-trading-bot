# data/forex_data.py

"""
Unified interface for Forex data.
Currently uses Yahoo Finance as the primary source.
"""

from pathlib import Path
import pandas as pd

from data.yfinance_downloader import get_forex_data_cached as _yf_get_data


def get_forex_data(
    symbol: str,
    timeframe: str = "15m",
    limit: int = 5000,
    force_download: bool = False,
    cache_dir: str = "data/downloadedData",
) -> pd.DataFrame:
    """
    Interfaz unificada para obtener datos de Forex.
    
    Args:
        symbol: Par de divisas (ej: "EURUSD", "GBPUSD", "XAUUSD")
        timeframe: Temporalidad ("1m", "5m", "15m", "30m", "1h", "1d")
        limit: Número de velas a descargar
        force_download: Forzar descarga (ignorar caché)
        cache_dir: Directorio de caché
    
    Returns:
        DataFrame con columnas: timestamp, open, high, low, close, volume
    """
    # Por ahora solo usamos Yahoo Finance
    # En el futuro se puede añadir lógica para elegir entre múltiples fuentes
    return _yf_get_data(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        force_download=force_download,
        cache_dir=cache_dir,
    )


# Alias para compatibilidad con la interfaz de crypto
get_forex_data_cached = get_forex_data


if __name__ == "__main__":
    # Test
    print("Testing unified Forex data interface...")
    
    df = get_forex_data("EURUSD", "15m", 100)
    print(f"\n✓ Downloaded {len(df)} candles")
    print(df.head())
