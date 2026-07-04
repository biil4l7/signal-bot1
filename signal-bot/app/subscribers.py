"""
Keeps track of everyone who has messaged the bot with /start, so signals
can be broadcast to all of them - not just one hardcoded chat ID.

Stored as a simple JSON file. NOTE: on Railway, attach a Volume mounted at
/app/data so this list survives redeploys (see README for steps). Without
a volume, redeploying will reset the subscriber list.
"""
import json
import os
import threading

_LOCK = threading.Lock()
_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "subscribers.json")


def _ensure_file():
    os.makedirs(os.path.dirname(_FILE), exist_ok=True)
    if not os.path.exists(_FILE):
        with open(_FILE, "w") as f:
            json.dump([], f)


def load_subscribers() -> list:
    _ensure_file()
    with _LOCK:
        with open(_FILE) as f:
            return json.load(f)


def add_subscriber(chat_id: int) -> bool:
    """Returns True if newly added, False if already subscribed."""
    _ensure_file()
    with _LOCK:
        with open(_FILE) as f:
            subs = json.load(f)
        if chat_id in subs:
            return False
        subs.append(chat_id)
        with open(_FILE, "w") as f:
            json.dump(subs, f)
        return True


def remove_subscriber(chat_id: int) -> bool:
    """Returns True if removed, False if wasn't subscribed."""
    _ensure_file()
    with _LOCK:
        with open(_FILE) as f:
            subs = json.load(f)
        if chat_id not in subs:
            return False
        subs.remove(chat_id)
        with open(_FILE, "w") as f:
            json.dump(subs, f)
        return True
