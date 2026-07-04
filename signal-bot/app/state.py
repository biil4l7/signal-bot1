"""
Keeps track of the last signal sent so the bot doesn't spam you with
the same alert repeatedly (cooldown window) or resend an alert for a
candle it already reported.
"""
from datetime import datetime, timedelta
from app import config

_last_signal_type = None
_last_signal_time = None
_last_candle_time = None


def should_send(signal: dict) -> bool:
    global _last_signal_type, _last_signal_time, _last_candle_time

    if signal is None:
        return False

    # Never re-alert the same candle twice (covers process restarts within a run)
    if _last_candle_time == signal["time"]:
        return False

    # Cooldown: same signal type repeated too soon
    if (
        _last_signal_type == signal["type"]
        and _last_signal_time is not None
        and datetime.utcnow() - _last_signal_time < timedelta(minutes=config.COOLDOWN_MINUTES)
    ):
        return False

    return True


def mark_sent(signal: dict) -> None:
    global _last_signal_type, _last_signal_time, _last_candle_time
    _last_signal_type = signal["type"]
    _last_signal_time = datetime.utcnow()
    _last_candle_time = signal["time"]
