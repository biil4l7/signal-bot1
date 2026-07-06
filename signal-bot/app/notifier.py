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

# A little personality per asset type, purely cosmetic.
_ASSET_EMOJI = {
    "BTC": "🟠",
    "ETH": "🔷",
    "SOL": "🟣",
    "XAU": "🥇",
    "EUR": "💶",
    "GBP": "💷",
    "USD": "💵",
}


def _emoji_for_symbol(symbol: str) -> str:
    base = symbol.split("/")[0].upper()
    return _ASSET_EMOJI.get(base, "📈")


def emoji_for_symbol(symbol: str) -> str:
    """Public wrapper so other modules (like the command listener) can use this."""
    return _emoji_for_symbol(symbol)


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


def broadcast_message(text: str) -> None:
    """
    Sends a message to every subscriber who has /start'd the bot.
    This is what makes the bot "public" - anyone who subscribes gets alerts.
    """
    from app import subscribers  # imported here to avoid circular import

    if not config.TELEGRAM_BOT_TOKEN:
        print("[notifier] Telegram not configured, skipping broadcast. Message was:")
        print(text)
        return

    chat_ids = subscribers.load_subscribers()
    if not chat_ids:
        print("[notifier] No subscribers yet, nothing to broadcast.")
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    for chat_id in chat_ids:
        try:
            requests.post(
                url,
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception as e:
            print(f"[notifier] Failed to send to {chat_id}: {e}")


def format_signal_message(symbol: str, signal: dict) -> str:
    asset_emoji = _emoji_for_symbol(symbol)
    direction_emoji = "🟢⬆️" if signal["type"] == "BUY" else "🔴⬇️"
    action_word = "BUY" if signal["type"] == "BUY" else "SELL"

    return (
        f"{direction_emoji} *{action_word} SIGNAL* {asset_emoji}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"*Symbol:* `{symbol}`\n"
        f"*Candle size:* `{config.TIMEFRAME}`\n"
        f"*Checked every:* `{config.CHECK_INTERVAL_SECONDS}s`\n"
        f"*Price:* `{signal['price']}`\n"
        f"*RSI:* `{signal['rsi']}`\n"
        f"*Candle time:* `{signal['time']}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"_Not financial advice - confirm before acting._"
    )


def format_review_message(symbol: str, record: dict, exit_price: float, correct: bool) -> str:
    """
    The 'was the last signal right?' feedback message, sent automatically
    once REVIEW_MINUTES has passed since a signal fired.
    """
    asset_emoji = _emoji_for_symbol(symbol)
    result_emoji = "✅" if correct else "❌"
    result_word = "CORRECT" if correct else "INCORRECT"

    entry_price = record["entry_price"]
    change_pct = round(100 * (exit_price - entry_price) / entry_price, 2)
    change_str = f"+{change_pct}%" if change_pct >= 0 else f"{change_pct}%"

    return (
        f"{result_emoji} *SIGNAL REVIEW* {asset_emoji}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"*Symbol:* `{symbol}`\n"
        f"*Called:* `{record['type']}` @ `{entry_price}`\n"
        f"*Now:* `{exit_price}`  ({change_str})\n"
        f"*Result:* {result_word} {result_emoji}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"_Based on price move after {config.REVIEW_MINUTES} min. Use /stats for your overall track record._"
    )
