"""
Signal rule:
  BUY  -> fast MA crosses ABOVE slow MA AND RSI is not overbought
  SELL -> fast MA crosses BELOW slow MA AND RSI is not oversold

Only evaluated on the LAST FULLY CLOSED candle (index -2), never the
still-forming candle (index -1), to avoid false/repainting signals.
"""
from app import config


def get_signal(df):
    if len(df) < max(config.SLOW_MA_PERIOD, config.RSI_PERIOD) + 2:
        return None  # not enough data yet

    prev = df.iloc[-3]   # candle before the last closed one
    last = df.iloc[-2]   # last fully closed candle

    crossed_up = prev["ma_fast"] <= prev["ma_slow"] and last["ma_fast"] > last["ma_slow"]
    crossed_down = prev["ma_fast"] >= prev["ma_slow"] and last["ma_fast"] < last["ma_slow"]

    if crossed_up and last["rsi"] < config.RSI_OVERBOUGHT:
        return {
            "type": "BUY",
            "price": last["close"],
            "time": last["datetime"],
            "rsi": round(last["rsi"], 2),
        }

    if crossed_down and last["rsi"] > config.RSI_OVERSOLD:
        return {
            "type": "SELL",
            "price": last["close"],
            "time": last["datetime"],
            "rsi": round(last["rsi"], 2),
        }

    return None
