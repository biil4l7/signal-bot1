"""
Entrypoint. Runs forever:
  1. Fetch latest candles
  2. Compute indicators
  3. Check for a BUY/SELL signal on the last CLOSED candle
  4. If new (not on cooldown) -> send Telegram alert
  5. Sleep, repeat

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


def run_once():
    df = fetch_candles(outputsize=100)
    df = compute_all(df)
    signal = get_signal(df)

    if signal and state.should_send(signal):
        message = format_signal_message(signal)
        send_telegram_message(message)
        state.mark_sent(signal)
        print(f"[main] Sent signal: {signal}")
    else:
        print(f"[main] No new signal at {df.iloc[-1]['datetime']}")


def main():
    print(f"[main] Starting signal bot for {config.SYMBOL} on {config.TIMEFRAME}")
    print(f"[main] Checking every {config.CHECK_INTERVAL_SECONDS} seconds")

    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[main] ERROR: {e}")
            traceback.print_exc()

        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
