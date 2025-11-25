# data/yfinance_downloader.py

"""
Yahoo Finance Data Downloader for Forex pairs.
Free, no API key required, works worldwide.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("WARNING: yfinance not installed. Run: pip install yfinance")


# Mapeo de símbolos a formato Yahoo Finance
SYMBOL_MAP = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "XAUUSD": "GC=F",  # Gold futures
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    "EURGBP": "EURGBP=X",
}

# Mapeo de timeframes
TIMEFRAME_MAP = {
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "90m": "90m",
    "1d": "1d",
}


def get_yfinance_data(
    symbol: str,
    timeframe: str = "15m",
    limit: int = 5000,
    period: str = "60d",  # Período máximo para datos intraday
) -> pd.DataFrame:
    """
    Descarga datos históricos desde Yahoo Finance.
    
    Args:
        symbol: Par de divisas (ej: "EURUSD", "GBPUSD", "XAUUSD")
        timeframe: Temporalidad ("1m", "5m", "15m", "30m", "1h", "1d")
        limit: Número de velas deseadas (aproximado)
        period: Período de descarga ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
                Para timeframes < 1d, máximo es "60d"
    
    Returns:
        DataFrame con columnas: timestamp, open, high, low, close, volume
    """
    if not YFINANCE_AVAILABLE:
        raise RuntimeError("yfinance package not installed")
    
    # Convertir símbolo a formato Yahoo Finance
    yf_symbol = SYMBOL_MAP.get(symbol, symbol)
    
    # Convertir timeframe
    yf_interval = TIMEFRAME_MAP.get(timeframe, timeframe)
    
    # Para timeframes intraday, Yahoo limita el período
    if timeframe in ["1m", "2m", "5m", "15m", "30m", "1h", "90m"]:
        # Máximo 60 días para datos intraday
        if period not in ["1d", "5d", "1mo", "3mo", "6mo", "60d"]:
            period = "60d"
    
    print(f"Descargando {symbol} ({yf_symbol}) desde Yahoo Finance...")
    print(f"Timeframe: {yf_interval}, Period: {period}")
    
    try:
        # Descargar datos
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, interval=yf_interval)
        
        if df.empty:
            raise RuntimeError(f"No se obtuvieron datos para {symbol}")
        
        # Resetear index (timestamp está en el index)
        df = df.reset_index()
        
        # Renombrar columnas
        df = df.rename(columns={
            'Date': 'timestamp',
            'Datetime': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
        })
        
        # Seleccionar solo las columnas que necesitamos
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Asegurar que timestamp es datetime con timezone
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Convertir a UTC si no tiene timezone
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
        
        # Ordenar y limpiar
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Limitar al número de velas solicitado
        if len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)
        
        print(f"✓ Descargados {len(df)} velas de {symbol} ({timeframe})")
        if len(df) > 0:
            print(f"  Rango: {df['timestamp'].iloc[0]} a {df['timestamp'].iloc[-1]}")
        
        return df
        
    except Exception as e:
        raise RuntimeError(f"Error al descargar datos de Yahoo Finance: {e}")


def get_forex_data_cached(
    symbol: str,
    timeframe: str = "15m",
    limit: int = 5000,
    force_download: bool = False,
    cache_dir: str = "data/downloadedData",
) -> pd.DataFrame:
    """
    Descarga datos de Forex con caché local (usando Yahoo Finance).
    
    Interfaz unificada compatible con get_datos_cripto_cached.
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    # Nombre de archivo
    safe_symbol = symbol.replace("/", "")
    cache_file = cache_path / f"{safe_symbol}_{timeframe}_forex.csv"
    
    # Intentar cargar desde caché
    if not force_download and cache_file.exists():
        try:
            df = pd.read_csv(cache_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Verificar si tenemos suficientes datos
            if len(df) >= limit:
                print(f"Usando datos locales desde {cache_file} ({len(df)} velas).")
                return df.tail(limit).reset_index(drop=True)
        except Exception as e:
            print(f"Error leyendo caché: {e}. Descargando datos frescos...")
    
    # Descargar datos frescos
    df = get_yfinance_data(symbol, timeframe, limit)
    
    # Guardar en caché
    try:
        df.to_csv(cache_file, index=False)
        print(f"Datos guardados en caché: {cache_file}")
    except Exception as e:
        print(f"Warning: No se pudo guardar caché: {e}")
    
    return df


if __name__ == "__main__":
    # Test básico
    print("Testing Yahoo Finance Forex downloader...")
    print("=" * 60)
    
    # Test 1: EURUSD
    try:
        print("\n1. Testing EURUSD 15m...")
        df = get_yfinance_data("EURUSD", "15m", 100)
        print(f"✓ Success! Shape: {df.shape}")
        print(df.head(3))
        print("...")
        print(df.tail(3))
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: GBPUSD
    try:
        print("\n2. Testing GBPUSD 1h...")
        df = get_yfinance_data("GBPUSD", "1h", 100)
        print(f"✓ Success! Shape: {df.shape}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: XAUUSD (Gold)
    try:
        print("\n3. Testing XAUUSD (Gold) 15m...")
        df = get_yfinance_data("XAUUSD", "15m", 100)
        print(f"✓ Success! Shape: {df.shape}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Cached download
    try:
        print("\n4. Testing cached download...")
        df = get_forex_data_cached("EURUSD", "15m", 100)
        print(f"✓ Success! Shape: {df.shape}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
