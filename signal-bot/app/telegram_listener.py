"""
Background listener that makes the bot respond to commands from ANY
Telegram user - this is what makes the bot "public" and interactive.
Runs in its own thread, separate from the main signal-checking loop.
"""
import time
import threading
import requests
from app import config, subscribers, history
from app.cache import get_cached_candles
from app.indicators import compute_all
from app.strategy import get_signal
from app.notifier import format_signal_message, emoji_for_symbol


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


def register_bot_commands() -> None:
    """
    Registers the command list with Telegram so it shows up in the native
    '/' menu button next to the message box - tappable, no typing needed.
    """
    if not config.TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "Subscribe to buy/sell alerts"},
        {"command": "stop", "description": "Unsubscribe from alerts"},
        {"command": "check", "description": "Check all symbols now (or /check BTC/USD for one)"},
        {"command": "list", "description": "Show tracked symbols"},
        {"command": "stats", "description": "See signal accuracy track record"},
        {"command": "help", "description": "Show what this bot does"},
    ]
    try:
        r = requests.post(url, json={"commands": commands}, timeout=10)
        r.raise_for_status()
        print("[listener] Bot command menu registered with Telegram")
    except Exception as e:
        print(f"[listener] Failed to register command menu: {e}")


def _normalize_symbol(raw: str) -> str:
    raw = raw.strip().upper()
    if "/" not in raw:
        raw = f"{raw}/USD"
    return raw


def _check_one_symbol(symbol: str) -> dict:
    """Fetches and evaluates one symbol. Returns a small result dict."""
    df = get_cached_candles(symbol, outputsize=100, ttl_seconds=config.CACHE_TTL_SECONDS)
    df = compute_all(df)
    signal = get_signal(df)
    last = df.iloc[-2]
    return {
        "symbol": symbol,
        "signal": signal,
        "price": last["close"],
        "rsi": round(last["rsi"], 2),
        "bullish": last["ma_fast"] > last["ma_slow"],
    }


def _handle_check_all(chat_id: int) -> None:
    _send(chat_id, f"🔎 Checking all {len(config.SYMBOLS)} tracked symbols, one sec...")

    lines = []
    for symbol in config.SYMBOLS:
        try:
            result = _check_one_symbol(symbol)
            emoji = emoji_for_symbol(symbol)

            if result["signal"]:
                action = result["signal"]["type"]
                arrow = "🟢⬆️ BUY" if action == "BUY" else "🔴⬇️ SELL"
                lines.append(f"{emoji} *{symbol}* — {arrow}  |  `{result['price']}`  RSI `{result['rsi']}`")
            else:
                trend = "↗️ bullish" if result["bullish"] else "↘️ bearish"
                lines.append(f"{emoji} *{symbol}* — {trend} (no fresh signal)  |  `{result['price']}`  RSI `{result['rsi']}`")

        except Exception as e:
            lines.append(f"⚠️ *{symbol}* — couldn't fetch data")
            print(f"[listener] /check all error for {symbol}: {e}")

        time.sleep(config.SECONDS_BETWEEN_SYMBOLS)

    header = "📊 *Current status - all tracked symbols:*\n━━━━━━━━━━━━━━━\n"
    footer = "\n━━━━━━━━━━━━━━━\n_Not financial advice - confirm before acting._"
    _send(chat_id, header + "\n".join(lines) + footer)


def _handle_check(chat_id: int, text: str) -> None:
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        _handle_check_all(chat_id)
        return

    symbol = _normalize_symbol(parts[1])
    # A couple of friendly aliases
    aliases = {"GOLD": "XAU/USD", "BITCOIN": "BTC/USD", "ETHEREUM": "ETH/USD", "SOLANA": "SOL/USD"}
    symbol = aliases.get(symbol.split("/")[0], symbol)

    _send(chat_id, f"🔎 Checking `{symbol}`, one sec...")

    try:
        df = get_cached_candles(symbol, outputsize=100, ttl_seconds=config.CACHE_TTL_SECONDS)
        df = compute_all(df)
        signal = get_signal(df)
        last = df.iloc[-2]

        if signal:
            _send(chat_id, format_signal_message(symbol, signal))
        else:
            trend = "bullish (fast MA above slow MA)" if last["ma_fast"] > last["ma_slow"] else "bearish (fast MA below slow MA)"
            _send(
                chat_id,
                f"📊 *{symbol}*\n"
                f"No fresh crossover right now.\n"
                f"Current trend: {trend}\n"
                f"Price: `{last['close']}`\n"
                f"RSI: `{round(last['rsi'], 2)}`",
            )
    except Exception as e:
        _send(chat_id, f"Couldn't fetch `{symbol}` - check the symbol is valid (e.g. EUR/USD, BTC/USD, XAU/USD).")
        print(f"[listener] /check error for {symbol}: {e}")


def _handle_stats(chat_id: int) -> None:
    overall = history.get_stats()

    lines = [
        "📈 *SIGNAL TRACK RECORD*",
        "━━━━━━━━━━━━━━━",
    ]

    if overall["total_evaluated"] == 0:
        lines.append("No signals have been graded yet.")
        lines.append(f"_Signals are reviewed {config.REVIEW_MINUTES} min after they fire._")
    else:
        lines.append(f"*Overall win rate:* `{overall['win_rate']}%`")
        lines.append(f"*Correct:* {overall['correct']}  |  *Incorrect:* {overall['incorrect']}")
        lines.append(f"*Pending review:* {overall['pending']}")
        lines.append("━━━━━━━━━━━━━━━")
        lines.append("*Per symbol:*")

        for symbol in config.SYMBOLS:
            s = history.get_stats(symbol)
            emoji = emoji_for_symbol(symbol)
            if s["total_evaluated"] == 0:
                lines.append(f"{emoji} {symbol} — no graded signals yet")
            else:
                lines.append(f"{emoji} {symbol} — `{s['win_rate']}%` ({s['correct']}/{s['total_evaluated']})")

    lines.append("━━━━━━━━━━━━━━━")
    lines.append("_Past accuracy isn't a guarantee of future results._")
    _send(chat_id, "\n".join(lines))


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
                f"Tap the menu button (☰) next to the message box to see all commands.",
            )
        else:
            _send(chat_id, "You're already subscribed. Send /stop to unsubscribe.")

    elif text.startswith("/stop"):
        removed = subscribers.remove_subscriber(chat_id)
        if removed:
            _send(chat_id, "You've been unsubscribed. Send /start anytime to rejoin.")
        else:
            _send(chat_id, "You weren't subscribed.")

    elif text.startswith("/check"):
        _handle_check(chat_id, text)

    elif text.startswith("/list"):
        _send(chat_id, f"📋 *Currently tracked symbols:*\n`{', '.join(config.SYMBOLS)}`")

    elif text.startswith("/stats"):
        _handle_stats(chat_id)

    elif text.startswith("/help"):
        _send(
            chat_id,
            "*What I do:*\n"
            "I watch price charts and alert you when a moving-average "
            "crossover + RSI condition suggests a possible buy or sell. "
            "I also grade my own past signals and track accuracy.\n\n"
            "*Commands:*\n"
            "/start - subscribe to alerts\n"
            "/stop - unsubscribe\n"
            "/check - check ALL tracked symbols right now\n"
            "/check SYMBOL - check just one, e.g. /check BTC/USD\n"
            "/list - see tracked symbols\n"
            "/stats - see signal accuracy track record\n\n"
            "_Not financial advice - always confirm before trading._",
        )


def _poll_loop() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        print("[listener] No TELEGRAM_BOT_TOKEN set, listener not starting.")
        return

    print("[listener] Listening for commands...")
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
    register_bot_commands()
    thread = threading.Thread(target=_poll_loop, daemon=True)
    thread.start()
