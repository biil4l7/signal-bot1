"""
Loads all settings from environment variables (.env locally, Railway
Variables tab in production). Nothing here is hardcoded.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # only does anything locally; Railway injects env vars directly

# --- Market data (Twelve Data) ---
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
SYMBOL = os.getenv("SYMBOL", "EUR/USD")          # e.g. EUR/USD, BTC/USD, AAPL
TIMEFRAME = os.getenv("TIMEFRAME", "15min")      # 1min,5min,15min,1h,4h,1day

# --- Strategy parameters ---
FAST_MA_PERIOD = int(os.getenv("FAST_MA_PERIOD", "9"))
SLOW_MA_PERIOD = int(os.getenv("SLOW_MA_PERIOD", "21"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
RSI_OVERBOUGHT = float(os.getenv("RSI_OVERBOUGHT", "70"))
RSI_OVERSOLD = float(os.getenv("RSI_OVERSOLD", "30"))

# --- Bot behaviour ---
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))  # 5 min
COOLDOWN_MINUTES = int(os.getenv("COOLDOWN_MINUTES", "60"))  # don't repeat same signal

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
