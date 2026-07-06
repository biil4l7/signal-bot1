"""
Entrypoint. Runs two things at once:
  1. A background listener thread that responds to commands from ANY
     Telegram user (public bot).
  2. The main loop: for each tracked symbol -
     a. Check for a fresh BUY/SELL signal and broadcast + record it
     b. Check if any older signals for this symbol are ready to be graded
        (did the market actually move the predicted direction?) and
        broadcast the result.

Run locally:   python main.py
Run on Railway: this file is the start command (see Procfile)
"""
import time
import traceback

from app import config
from app.cache import get_cached_candles
from app.indicators import compute_all
from app.strategy import get_signal
from app.notifier import broadcast_message, format_signal_message, format_review_message, emoji_for_symbol
from app import state, history
from app.telegram_listener import start_listener_thread


def evaluate_due_signals(symbol: str, current_price: float):
    due = history.get_due_for_review(symbol, config.REVIEW_MINUTES)
    for index, record in due:
        if record["type"] == "BUY":
            correct = current_price > record["entry_price"]
        else:
            correct = current_price < record["entry_price"]

        history.mark_evaluated(index, current_price, correct)
        message = format_review_message(symbol, record, current_price, correct)
        broadcast_message(message)
        print(f"[main] Graded {symbol} {record['type']} as {'CORRECT' if correct else 'INCORRECT'}")


def check_symbol(symbol: str):
    df = get_cached_candles(symbol, outputsize=100, ttl_seconds=config.CACHE_TTL_SECONDS)
    df = compute_all(df)
    signal = get_signal(df)
    current_price = df.iloc[-1]["close"]

    if signal and state.should_send(symbol, signal):
        message = format_signal_message(symbol, signal)
        broadcast_message(message)
        state.mark_sent(symbol, signal)
        history.record_signal(symbol, signal)
        print(f"[main] Broadcast {signal['type']} signal for {symbol}")
    else:
        print(f"[main] {symbol}: no new signal at {df.iloc[-1]['datetime']}")

    evaluate_due_signals(symbol, current_price)


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
