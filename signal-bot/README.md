# Signal Bot — Buy/Sell Alert Bot

A personal-use bot that watches a market (forex/crypto/stock) and sends you
a **Telegram message** when a buy or sell condition is met. It never trades
for you — you always decide. There is no dashboard/UI; Telegram *is* the
interface.

---

## 1. How it works (in order)

1. Every `CHECK_INTERVAL_SECONDS` (default 5 min), the bot downloads the
   latest candles for your chosen symbol from **Twelve Data**.
2. It calculates two moving averages (fast/slow) and RSI.
3. It looks **only at the last fully closed candle** (never the one still
   forming) to decide if a crossover happened.
4. Rule:
   - **BUY** → fast MA crosses above slow MA, and RSI is not overbought
   - **SELL** → fast MA crosses below slow MA, and RSI is not oversold
5. If a signal fires and it isn't a repeat within your cooldown window, it
   sends you a Telegram message like:

   ```
   🟢 BUY SIGNAL
   Symbol: EUR/USD
   Timeframe: 15min
   Price: 1.0854
   RSI: 54.2
   Candle time: 2026-07-04 14:15:00
   ```

6. It sleeps, then repeats forever.

There is no web page, no button to click — the "interface" is your Telegram
chat. This is intentional: it's the least disruptive option (a push
notification, not a screen you have to babysit).

---

## 2. Project structure

```
signal-bot/
├── app/
│   ├── __init__.py
│   ├── config.py        # reads all settings from environment variables
│   ├── data_fetcher.py  # gets candle data from Twelve Data API
│   ├── indicators.py    # moving averages + RSI calculations
│   ├── strategy.py      # turns indicators into BUY/SELL/None
│   ├── notifier.py      # sends the Telegram message
│   └── state.py         # cooldown logic so you don't get spammed
├── main.py               # the loop that ties it all together
├── requirements.txt
├── Procfile              # tells Railway how to run the bot
├── .env.example          # template — copy to .env locally
├── .gitignore
└── README.md
```

---

## 3. One-time setup

### A. Get a Twelve Data API key (free)
1. Go to https://twelvedata.com and create a free account.
2. Copy your API key from the dashboard.

### B. Create a Telegram bot (for alerts)
1. In Telegram, message **@BotFather** → `/newbot` → follow the prompts.
2. Copy the token it gives you.
3. Send any message to your new bot (e.g. "hi").
4. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
   and find `"chat":{"id": ...}` — copy that number.

### C. Fill in your environment variables
Copy `.env.example` to `.env` and fill in:
- `TWELVE_DATA_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- Adjust `SYMBOL`, `TIMEFRAME`, and strategy numbers if you want.

---

## 4. Run it locally (test before deploying)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

You should see log lines every few minutes, and a Telegram message the next
time a real signal fires (this can take hours/days depending on the market —
that's normal, it means it's not giving you false signals).

---

## 5. Deploy on Railway

1. Push this folder to a GitHub repo (`.env` is gitignored — never commit it).
2. On Railway: **New Project → Deploy from GitHub repo** → select this repo.
3. Railway auto-detects Python and reads the `Procfile`.
4. Go to your service → **Variables** tab → add every key from `.env.example`
   with your real values (this replaces the `.env` file in the cloud).
5. Deploy. Check the **Deployments → Logs** tab to see it running.
6. Because it's declared as a `worker` process (not a web server), it runs
   continuously in the background — no public URL needed.

---

## 6. Tuning it to reduce noise or increase sensitivity

All in your `.env` / Railway Variables, no code changes needed:

| Variable | Effect |
|---|---|
| `FAST_MA_PERIOD` / `SLOW_MA_PERIOD` | Bigger gap between them = fewer, more significant signals |
| `RSI_OVERBOUGHT` / `RSI_OVERSOLD` | Wider band (e.g. 80/20) = stricter filter, fewer signals |
| `TIMEFRAME` | Higher timeframe (1h, 4h) = fewer but more reliable signals |
| `COOLDOWN_MINUTES` | Minimum time between repeated same-direction alerts |
| `CHECK_INTERVAL_SECONDS` | How often it polls for new data |

---

## 7. Important honesty note

This bot tells you when **your chosen rule** is true — it does not predict
the market. Moving average + RSI crossovers are a common, well-understood
starting strategy, but no indicator combination is reliably profitable on
its own. Treat every alert as "worth looking at," not "guaranteed correct."
This is not financial advice, and you place any trade yourself.
