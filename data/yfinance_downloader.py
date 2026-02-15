import yfinance as yf
import pandas as pd
from typing import Optional

from data.cache import market_data_cache


def get_yfinance_data(
    symbol: str, timeframe: str = "1d", limit: int = 1000, period: str = "1y"
) -> Optional[pd.DataFrame]:
    """Download OHLCV data from yfinance with caching."""
    cache_key = f"yfinance:{symbol}:{timeframe}:{period}:{limit}"
    cached = market_data_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        interval = timeframe

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            return None

        # Lowercase column names
        df.columns = [c.lower() for c in df.columns]

        # Convert index to timestamp column for strategy compatibility
        df.index.name = "timestamp"
        df = df.reset_index()

        required = ["timestamp", "open", "high", "low", "close", "volume"]
        if not all(c in df.columns for c in required):
            return None

        result = df[required]
        market_data_cache.set(cache_key, result)
        return result

    except Exception as e:
        print(f"Error downloading data for {symbol}: {e}")
        return None
