# Trading Bot (Paper Trading Only)

This is a practice trading bot. It does **not** use real money and **cannot**
place real orders. Everything it does is pretend — like a flight simulator
for pilots.

## What the bot does

Every morning before the market opens, the bot:

1. **Scans** for stocks that are jumping up before the market opens
   (up 4% or more, with lots of shares already trading).
2. **Filters** them through the 5 Pillars — five checks a stock must pass
   to be worth trading.
3. **Plans** each trade before it happens: where to buy, where to get out
   if it's wrong (stop-loss), and where to take profit (target).
4. **Manages risk automatically** — it will stop itself for the day if
   things go badly, no arguing.
5. **Writes everything down** in a daily log file so you can review later.

## How the strategy works (the 5 Pillars)

A stock only gets traded if it passes **all five** of these:

1. **Volume** — trading at least 5x more shares than normal.
2. **Momentum** — already up 10% or more today.
3. **Real news** — there is a genuine reason (earnings, FDA approval,
   partnership). Rumors don't count.
4. **Price** — between $2 and $20 per share.
5. **Small float** — fewer than ~10 million shares available (small supply
   means buying pressure moves the price more).

**The entry (called "Gap and Go"):** if a passing stock breaks above its
pre-market high after the open, the bot "buys" there. The stop-loss goes
just below where it broke out from. The profit target is set so a win
makes about twice what a loss would cost ($100 win vs $50 risk).

**Position size:** the bot figures out how many shares to "buy" so that
even if the stop-loss hits, you lose no more than $50.

## The risk rules (automatic, no exceptions)

- Never risk more than **$50** on a single trade.
- Each trade aims to make **$100**.
- If the day's total losses reach **-$100**, the bot stops for the day.
- If it loses **3 trades in a row**, it stops for the day.

When a rule trips, the bot logs exactly why it stopped.

## How to run it (paper/simulation mode)

You need Python 3. No API keys needed for simulation mode.

```bash
cd ~/workspace/trading-bot
pip install -r requirements.txt   # one time only
python3 bot.py                    # runs one pretend morning session
```

To use your own pretend candidates:

```bash
python3 bot.py --watchlist-file sample_watchlist.json
```

The log for the day lands in `logs/YYYY-MM-DD.log` — open it to see every
scan result, trade plan, and decision.

### Alpaca paper mode (still pretend money, but real market data)

1. Open a free Alpaca paper-trading account and get API keys.
2. Set them without saving them in any file:
   `export ALPACA_API_KEY=...` and `export ALPACA_API_SECRET=...`
3. Run: `python3 bot.py --mode alpaca --watchlist AAPL TSLL`

This places orders on Alpaca's **paper** system only. The bot refuses to
talk to any live-trading address — that check is built into the code.

## What would be needed for live mode later

Live mode is **not built** and **not enabled**. Turning this into a
real-money bot would need, at minimum:

1. **Antonio's explicit, separate approval** — never enable it silently
   or by default.
2. Real brokerage API keys, stored securely (never in chat, never in a file
   that gets shared).
3. A re-test of every safety rule, plus new ones a live bot needs
   (like a kill switch and max daily orders).

Until all three happen, this stays a simulator.

## Limitations (honest list)

- **Simulation mode invents prices.** It tests that the plumbing works
  (scan -> filter -> plan -> risk rules -> log). It says nothing about
  whether the strategy actually makes money.
- **Alpaca's free data has no float numbers and no gap screener**, so in
  Alpaca mode the bot checks a watchlist you give it, and the float check
  fails closed (no trade) unless float data is supplied another way.
- **News checking is basic.** In simulation, the "news" is typed in by
  hand. A serious version would plug in a real news feed.
- **No Level 2 / order-book reading** in this build — entries use the
  pre-market high break only.
- **This is educational software, not financial advice.** Most day
  traders lose money. Prove things in simulation first — that's what
  this bot is for.
