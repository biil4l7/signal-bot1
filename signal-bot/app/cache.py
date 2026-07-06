"""
Simple in-memory cache for candle data, shared between the scheduled loop
and on-demand /check commands. Without this, both paths hit Twelve Data
independently and can burn through the free-tier rate limit fast.
"""
import time
import threading
from app.data_fetcher import fetch_candles

_LOCK = threading.Lock()
_CACHE = {}  # symbol -> (fetched_at_epoch_seconds, dataframe)


def get_cached_candles(symbol: str, outputsize: int = 100, ttl_seconds: int = 60):
    """
    Returns cached candle data if it's fresher than ttl_seconds, otherwise
    fetches fresh data from Twelve Data and updates the cache.
    """
    now = time.time()
    with _LOCK:
        cached = _CACHE.get(symbol)
        if cached and (now - cached[0]) < ttl_seconds:
            return cached[1]

    df = fetch_candles(symbol, outputsize=outputsize)

    with _LOCK:
        _CACHE[symbol] = (now, df)

    return df
