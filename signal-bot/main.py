"""
Entrypoint. Runs two things at once:
  1. A background listener thread that responds to /start and /stop from
     ANY Telegram user - this is what makes the bot public.
  2. The main loop: for each tracked symbol, check for a BUY/SELL signal
     and broadcast it to every subscriber.

Run locally:   python main.py
Run on Railway: this file is the start command (see Procfile)
"""
import time
import traceback

from app import config
from app.data_fetcher import fetch_candles
from app.indicators import compute_all
from app.strategy import get_signal
from app.notifier import broadcast_message, format_signal_message
from app import state
from app.telegram_listener import start_listener_thread


def check_symbol(symbol: str):
    df = fetch_candles(symbol, outputsize=100)
    df = compute_all(df)
    signal = get_signal(df)

    if signal and state.should_send(symbol, signal):
        message = format_signal_message(symbol, signal)
        broadcast_message(message)
        state.mark_sent(symbol, signal)
        print(f"[main] Broadcast {signal['type']} signal for {symbol}")
    else:
        print(f"[main] {symbol}: no new signal at {df.iloc[-1]['datetime']}")


def run_once():
    for symbol in config.SYMBOLS:
        try:
            check_symbol(symbol)
        except Exception as e:
            print(f"[main] ERROR checking {symbol}: {e}")
            traceback.print_exc()

        time.sleep(config.SECONDS_BETWEEN_SYMBOLS)


def main():
    print(f"[main] Starting PUBLIC signal bot for: {', '.join(config.SYMBOLS)}")
    print(f"[main] Timeframe: {config.TIMEFRAME}, checking every {config.CHECK_INTERVAL_SECONDS} seconds")

    # Start listening for /start and /stop from anyone, in the background
    start_listener_thread()

    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[main] ERROR: {e}")
            traceback.print_exc()

        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
