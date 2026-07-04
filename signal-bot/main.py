"""
Entrypoint. Runs forever:
  1. For each symbol in config.SYMBOLS:
     a. Fetch latest candles
     b. Compute indicators
     c. Check for a BUY/SELL signal on the last CLOSED candle
     d. If new (not on cooldown) -> send a Telegram alert for that symbol
  2. Sleep, repeat

Run locally:   python main.py
Run on Railway: this file is the start command (see Procfile)
"""
import time
import traceback

from app import config
from app.data_fetcher import fetch_candles
from app.indicators import compute_all
from app.strategy import get_signal
from app.notifier import send_telegram_message, format_signal_message
from app import state


def check_symbol(symbol: str):
    df = fetch_candles(symbol, outputsize=100)
    df = compute_all(df)
    signal = get_signal(df)

    if signal and state.should_send(symbol, signal):
        message = format_signal_message(symbol, signal)
        send_telegram_message(message)
        state.mark_sent(symbol, signal)
        print(f"[main] Sent {signal['type']} signal for {symbol}")
    else:
        print(f"[main] {symbol}: no new signal at {df.iloc[-1]['datetime']}")


def run_once():
    for symbol in config.SYMBOLS:
        try:
            check_symbol(symbol)
        except Exception as e:
            print(f"[main] ERROR checking {symbol}: {e}")
            traceback.print_exc()

        # Small delay between symbols to respect Twelve Data's rate limit
        time.sleep(config.SECONDS_BETWEEN_SYMBOLS)


def main():
    print(f"[main] Starting signal bot for: {', '.join(config.SYMBOLS)}")
    print(f"[main] Timeframe: {config.TIMEFRAME}, checking every {config.CHECK_INTERVAL_SECONDS} seconds")

    send_telegram_message(
        f"✅ *Signal bot is online*\n"
        f"Tracking: `{', '.join(config.SYMBOLS)}`\n"
        f"Timeframe: `{config.TIMEFRAME}`\n"
        f"Checking every {config.CHECK_INTERVAL_SECONDS} seconds."
    )

    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[main] ERROR: {e}")
            traceback.print_exc()

        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
