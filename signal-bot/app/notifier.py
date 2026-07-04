"""
Sends alerts to your Telegram. Setup (one-time, 2 minutes):
  1. Open Telegram, search "BotFather", send /newbot, follow prompts.
     -> copy the token it gives you into TELEGRAM_BOT_TOKEN
  2. Send any message to your new bot.
  3. Visit https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
     -> find "chat":{"id": ...} and copy that number into TELEGRAM_CHAT_ID
"""
import requests
from app import config


def send_telegram_message(text: str) -> None:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[notifier] Telegram not configured, skipping. Message was:")
        print(text)
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[notifier] Failed to send Telegram message: {e}")


def format_signal_message(signal: dict) -> str:
    emoji = "🟢" if signal["type"] == "BUY" else "🔴"
    return (
        f"{emoji} *{signal['type']} SIGNAL*\n"
        f"Symbol: `{config.SYMBOL}`\n"
        f"Timeframe: `{config.TIMEFRAME}`\n"
        f"Price: `{signal['price']}`\n"
        f"RSI: `{signal['rsi']}`\n"
        f"Candle time: `{signal['time']}`\n\n"
        f"_This is not financial advice. Confirm before acting._"
    )
