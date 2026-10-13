"""Central configuration for the 5-Pillars paper trading bot.

Everything the strategy and risk rules need lives here, in one place.
PAPER TRADING ONLY — this bot never touches real money.
"""

# --- Safety: paper endpoints only. The order executor refuses anything else. ---
PAPER_API_BASE_URL = "https://paper-api.alpaca.markets"
DATA_API_BASE_URL = "https://data.alpaca.markets"

# --- Mode: "simulation" (default, needs no keys) or "alpaca_paper" ---
# "alpaca_paper" still never uses real money — it uses Alpaca's free
# paper-trading account. It needs ALPACA_API_KEY and ALPACA_API_SECRET set.
MODE = "simulation"

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
