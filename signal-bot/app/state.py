"""
Keeps track of the last signal sent PER SYMBOL so the bot doesn't spam you
with the same alert repeatedly (cooldown window) or resend an alert for a
candle it already reported - each symbol tracked independently.
"""
from datetime import datetime, timedelta
from app import config

# symbol -> {"type": "BUY"/"SELL", "sent_at": datetime, "candle_time": ...}
_last_signal_by_symbol = {}


def should_send(symbol: str, signal: dict) -> bool:
    if signal is None:
        return False

    last = _last_signal_by_symbol.get(symbol)
    if last is None:
        return True

    # Never re-alert the same candle twice for this symbol
    if last["candle_time"] == signal["time"]:
        return False

    # Cooldown: same signal type repeated too soon for this symbol
    if (
        last["type"] == signal["type"]
        and datetime.utcnow() - last["sent_at"] < timedelta(minutes=config.COOLDOWN_MINUTES)
    ):
        return False

    return True


def mark_sent(symbol: str, signal: dict) -> None:
    _last_signal_by_symbol[symbol] = {
        "type": signal["type"],
        "sent_at": datetime.utcnow(),
        "candle_time": signal["time"],
    }
