"""Fear & Greed Index data provider using alternative.me API."""

from typing import Any, Dict, Optional

import requests

from data.cache import market_data_cache

FEAR_GREED_API_URL = "https://api.alternative.me/fng/"


def get_fear_greed_index(limit: int = 1) -> Optional[Dict[str, Any]]:
    """
    Fetch the Crypto Fear & Greed Index.

    Args:
        limit: Number of data points to return (default 1 = latest only).

    Returns:
        Dict with keys: value (0-100), value_classification, timestamp.
        None on error.
    """
    cache_key = f"fear_greed:{limit}"
    cached = market_data_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        response = requests.get(
            FEAR_GREED_API_URL,
            params={"limit": limit, "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if "data" not in data or not data["data"]:
            return None

        result = {
            "data": [
                {
                    "value": int(entry["value"]),
                    "value_classification": entry["value_classification"],
                    "timestamp": int(entry["timestamp"]),
                }
                for entry in data["data"]
            ]
        }

        # Cache for 10 minutes (index updates daily)
        market_data_cache.set(cache_key, result, ttl=600)
        return result

    except Exception:
        return None
