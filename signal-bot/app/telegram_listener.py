"""
Background listener that makes the bot respond to /start and /stop from
ANY Telegram user - this is what makes the bot "public." Runs in its own
thread, separate from the main signal-checking loop.
"""
import time
import threading
import requests
from app import config, subscribers


def _send(chat_id: int, text: str) -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as e:
        print(f"[listener] Failed to send message: {e}")


def _handle_message(message: dict) -> None:
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text.startswith("/start"):
        newly_added = subscribers.add_subscriber(chat_id)
        symbols_list = ", ".join(config.SYMBOLS)
        if newly_added:
            _send(
                chat_id,
                f"✅ *You're subscribed!*\n\n"
                f"You'll get buy/sell alerts for:\n`{symbols_list}`\n"
                f"Timeframe: `{config.TIMEFRAME}`\n\n"
                f"Send /stop anytime to unsubscribe.",
            )
        else:
            _send(chat_id, "You're already subscribed. Send /stop to unsubscribe.")

    elif text.startswith("/stop"):
        removed = subscribers.remove_subscriber(chat_id)
        if removed:
            _send(chat_id, "You've been unsubscribed. Send /start anytime to rejoin.")
        else:
            _send(chat_id, "You weren't subscribed.")


def _poll_loop() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        print("[listener] No TELEGRAM_BOT_TOKEN set, listener not starting.")
        return

    print("[listener] Listening for /start and /stop commands...")
    offset = None
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"

    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(url, params=params, timeout=35)
            data = resp.json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message")
                if message:
                    _handle_message(message)

        except Exception as e:
            print(f"[listener] Error polling Telegram: {e}")
            time.sleep(5)


def start_listener_thread() -> None:
    thread = threading.Thread(target=_poll_loop, daemon=True)
    thread.start()
