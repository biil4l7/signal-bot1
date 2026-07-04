"""
Pulls candle (OHLC) data from Twelve Data's REST API.
Works from anywhere with internet access - no broker terminal required.
Free tier: https://twelvedata.com/pricing (8 requests/minute - the bot
spaces out requests across symbols to respect this).
"""
import requests
import pandas as pd
from app import config

BASE_URL = "https://api.twelvedata.com/time_series"


def fetch_candles(symbol: str, outputsize: int = 100) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: datetime, open, high, low, close
    Sorted oldest -> newest, for the given symbol.
    """
    params = {
        "symbol": symbol,
        "interval": config.TIMEFRAME,
        "outputsize": outputsize,
        "apikey": config.TWELVE_DATA_API_KEY,
    }
    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if "values" not in data:
        raise RuntimeError(f"Twelve Data error: {data}")

    df = pd.DataFrame(data["values"])
    df = df.rename(columns={"datetime": "datetime"})
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    return df
