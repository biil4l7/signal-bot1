"""
Records every signal sent, then later checks whether the market actually
moved the predicted direction - this is what powers the "was this signal
right?" feedback and /stats command.
"""
import json
import os
import threading
from datetime import datetime, timedelta

_LOCK = threading.Lock()
_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "signal_history.json")


def _ensure_file():
    os.makedirs(os.path.dirname(_FILE), exist_ok=True)
    if not os.path.exists(_FILE):
        with open(_FILE, "w") as f:
            json.dump([], f)


def _load() -> list:
    _ensure_file()
    with open(_FILE) as f:
        return json.load(f)


def _save(records: list) -> None:
    with open(_FILE, "w") as f:
        json.dump(records, f)


def record_signal(symbol: str, signal: dict) -> None:
    with _LOCK:
        records = _load()
        records.append({
            "symbol": symbol,
            "type": signal["type"],
            "entry_price": signal["price"],
            "entry_time": datetime.utcnow().isoformat(),
            "candle_time": str(signal["time"]),
            "evaluated": False,
            "correct": None,
            "exit_price": None,
        })
        _save(records)


def get_due_for_review(symbol: str, review_minutes: int) -> list:
    """Returns [(index, record), ...] for this symbol's un-evaluated signals
    that are old enough to grade now."""
    now = datetime.utcnow()
    with _LOCK:
        records = _load()
        due = []
        for i, r in enumerate(records):
            if r["symbol"] != symbol or r["evaluated"]:
                continue
            entry_time = datetime.fromisoformat(r["entry_time"])
            if now - entry_time >= timedelta(minutes=review_minutes):
                due.append((i, r))
        return due


def mark_evaluated(index: int, exit_price: float, correct: bool) -> None:
    with _LOCK:
        records = _load()
        records[index]["evaluated"] = True
        records[index]["exit_price"] = exit_price
        records[index]["correct"] = correct
        _save(records)


def get_stats(symbol: str = None) -> dict:
    records = _load()
    if symbol:
        records = [r for r in records if r["symbol"] == symbol]

    evaluated = [r for r in records if r["evaluated"]]
    correct = [r for r in evaluated if r["correct"]]
    total = len(evaluated)
    win_rate = round(100 * len(correct) / total, 1) if total else None

    return {
        "total_evaluated": total,
        "correct": len(correct),
        "incorrect": total - len(correct),
        "win_rate": win_rate,
        "pending": len([r for r in records if not r["evaluated"]]),
    }
