"""
Pure calculation functions - no network calls, easy to unit test.
"""
import pandas as pd
from app import config


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    df["ma_fast"] = df["close"].rolling(config.FAST_MA_PERIOD).mean()
    df["ma_slow"] = df["close"].rolling(config.SLOW_MA_PERIOD).mean()
    return df


def add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(config.RSI_PERIOD).mean()
    avg_loss = loss.rolling(config.RSI_PERIOD).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    df = add_moving_averages(df)
    df = add_rsi(df)
    return df
