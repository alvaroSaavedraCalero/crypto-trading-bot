"""Market data endpoints."""

import sys
from pathlib import Path

import yfinance as yf
from fastapi import APIRouter, HTTPException, Query

# Add project root to path for imports
project_root = str(Path(__file__).parent.parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.yfinance_downloader import get_yfinance_data
from data.cache import market_data_cache

router = APIRouter()


@router.get("/prices/{symbol}")
async def get_current_price(symbol: str):
    """Fetch current price for a symbol via yfinance."""
    cache_key = f"price:{symbol}"
    cached = market_data_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = getattr(info, "last_price", None)
        if price is None:
            raise HTTPException(status_code=404, detail=f"Price not available for {symbol}")

        result = {
            "symbol": symbol,
            "price": float(price),
            "currency": getattr(info, "currency", "USD"),
        }
        market_data_cache.set(cache_key, result, ttl=60)
        return result

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail=f"Could not fetch price for {symbol}")


@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query(default="1d", description="Candle interval"),
    period: str = Query(default="1mo", description="Lookback period"),
    limit: int = Query(default=500, le=5000, description="Max candles"),
):
    """Fetch OHLCV data for a symbol."""
    df = get_yfinance_data(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        period=period,
    )

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

    records = df.head(limit).to_dict(orient="records")
    # Convert timestamps to ISO strings
    for record in records:
        if hasattr(record["timestamp"], "isoformat"):
            record["timestamp"] = record["timestamp"].isoformat()

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "period": period,
        "count": len(records),
        "data": records,
    }
