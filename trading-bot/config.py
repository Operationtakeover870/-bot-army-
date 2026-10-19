"""Central configuration for the 5-Pillars paper trading bot.

Everything the strategy and risk rules need lives here, in one place.
PAPER TRADING ONLY — this bot never touches real money.
"""

# --- Safety: paper endpoints only. The order executor refuses anything else. ---
PAPER_API_BASE_URL = "https://paper-api.alpaca.markets"
DATA_API_BASE_URL = "https://data.alpaca.markets"

# --- Mode: "simulation" (needs no keys) or "alpaca_paper" ---
# "alpaca_paper" still never uses real money — it uses Alpaca's free
# paper-trading account. It needs ALPACA_API_KEY and ALPACA_API_SECRET set.
MODE = "alpaca_paper"

# --- Strategy: the 5 Pillars (from the day-trading study notes) ---
MIN_RELATIVE_VOLUME = 5.0      # Pillar 1: volume >= 5x the stock's average
MIN_DAY_GAIN_PCT = 10.0        # Pillar 2: up >= 10% on the day
REQUIRE_NEWS_CATALYST = True   # Pillar 3: real, verifiable news (no rumors)
MIN_PRICE = 2.0                # Pillar 4: price between $2 and $20
MAX_PRICE = 20.0
MAX_FLOAT_SHARES = 10_000_000  # Pillar 5: float under ~10M shares

# --- Pre-market scanner ---
PREMARKET_MIN_GAP_PCT = 4.0    # gapping up at least 4% pre-market
PREMARKET_MIN_SHARES = 100_000 # with at least 100K pre-market shares traded

# --- Technical indicator confirmation filters (Day Trading Overview study) ---
# The 5 Pillars stay the primary gate; these confirm entries when enough
# price history exists. All are vetoes: one fail = no trade.
IND_RSI_PERIOD = 14
IND_RSI_MIN = 45.0             # veto below: momentum fading, don't chase it
IND_RSI_MAX = 80.0             # veto above: parabolic exhaustion (Cameron-style
                               # momentum wants strength, not a vertical blow-off)
IND_MACD_FAST = 12
IND_MACD_SLOW = 26
IND_MACD_SIGNAL = 9            # require MACD line > signal line (bullish)
IND_SMA_PERIOD = 20            # require price above SMA(20) (uptrend)
IND_BB_PERIOD = 20
IND_BB_STD = 2.0
IND_BB_MIN_BANDWIDTH = 0.06    # veto "squeeze" chop below 6% bandwidth
IND_MIN_BARS = 35              # bars needed before confirmation runs

# --- Risk: HARD RULES. The risk manager enforces these; nothing overrides them. ---
MAX_RISK_PER_TRADE = 50.0      # never risk more than $50 on one trade
PROFIT_TARGET_PER_TRADE = 100.0  # aim to make $100 per trade (2:1 reward:risk)
DAILY_MAX_LOSS = -100.0        # down $100 on the day -> done, no exceptions
MAX_CONSECUTIVE_LOSSES = 3     # 3 losing trades in a row -> done for the day

# --- Session window (Eastern Time). The framework trades the morning only. ---
SESSION_START_ET = "09:30"
SESSION_END_ET = "10:30"

# --- Logging ---
LOG_DIR = "logs"

# --- Simulation defaults (only used in simulation mode) ---
SIM_STARTING_CASH = 10_000.0
SIM_RANDOM_SEED = 42
