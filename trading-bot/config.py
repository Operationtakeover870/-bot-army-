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
# CHANCES REVISION (Nov 1, 2026 — Antonio: "they gotta take chances").
# The strict Pillars could never pass on free Alpaca data: the feed
# cannot supply float at all, news was never wired in, and relative
# volume was hardcoded 0.0 — so the bot sat flat forever. The gates
# below are what free data CAN actually measure. The original strict
# values are kept in comments for reference; the RISK cage below did
# NOT change (still $50/trade, -$100 daily halt, 3-loss halt).
MIN_RELATIVE_VOLUME = 2.0      # was 5.0 strict: volume >= 2x average
MIN_DAY_GAIN_PCT = 5.0         # was 10.0 strict: up >= 5% on the day
REQUIRE_NEWS_CATALYST = False  # was True: news is now a logged bonus,
                               # not a veto (feed tries Alpaca news API)
MIN_PRICE = 1.0                # was $2: price between $1 and $30
MAX_PRICE = 30.0               # was $20
FLOAT_VETO = False             # was fail-closed: float is not in free
                               # Alpaca data, so unknown (or large) float
                               # is logged as a warning, not a veto
MAX_FLOAT_SHARES = 10_000_000  # reference only, while FLOAT_VETO is off

# --- Default scan universe (alpaca mode, when no --watchlist is given) ---
# Free Alpaca data has no gap screener, so the feed checks these symbols
# directly. Liquid names; the price/gap/volume gates do the filtering.
# Antonio can override with: python3 bot.py --mode alpaca --watchlist SYM1 SYM2
DEFAULT_WATCHLIST = [
    "SOFI", "PLTR", "MARA", "RIOT", "HOOD", "COIN", "MSTR", "GME", "AMC",
    "BB", "NOK", "LCID", "RIVN", "NIO", "XPEV", "LI", "OPEN", "CVNA",
    "BYND", "PTON", "FUBO", "AFRM", "UPST", "DKNG", "PENN", "RBLX", "U",
    "SE", "SHOP", "SQ", "PYPL", "AMD", "NVDA", "TSLA", "AAPL", "MSFT",
    "AMZN", "META", "ARM", "SMCI", "DELL", "F", "GM", "INTC", "WBD",
    "PARA", "SNAP", "PINS", "ROKU", "UBER", "ABNB", "MRNA", "BBAI", "SOUN",
]

# --- Pre-market scanner ---
PREMARKET_MIN_GAP_PCT = 4.0    # gapping up at least 4% pre-market
PREMARKET_MIN_SHARES = 100_000 # with at least 100K pre-market shares traded

# --- Technical indicator confirmation filters (Day Trading Overview study) ---
# CHANCES REVISION (Nov 1, 2026): confirmation is ADVISORY, not a veto.
# On realistic choppy closes the old veto-all behavior still blocked
# trades (MACD lagging a fresh move, Bollinger "squeeze" on chop) —
# which would have left the bot flat again despite the relaxed gates.
# The checks still run and are logged on every signal; the RISK cage
# ($50/trade, -$100 halt, 3-loss halt) is the protection now, not the
# indicators. Set IND_CONFIRM_VETO = True to restore strict vetoes.
IND_CONFIRM_VETO = False
IND_RSI_PERIOD = 14
IND_RSI_MIN = 40.0             # was 45: momentum zone widened for chances tier
IND_RSI_MAX = 90.0             # was 80: gapping stocks run hot on daily bars;
                               # 90 still vetoes a vertical blow-off
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
