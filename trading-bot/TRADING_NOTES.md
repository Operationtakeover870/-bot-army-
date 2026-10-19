# TRADING NOTES — Day Trading Overview lessons installed (Oct 19, 2026)

Study material: Antonio's imported "Day Trading Overview" (school work for ICE
and the bots). Installed into Bot #1's code as surgical additions. The
5-Pillars Gap-and-Go strategy is unchanged as the primary gate; everything
below confirms or protects it.

## What was added

**indicators.py (new)** — technical indicator confirmation filters, pure
stdlib, no new dependencies:
- RSI(14) — momentum zone 45-80: veto below 45 (momentum fading) and
  above 80 (parabolic exhaustion). A gap stock always has elevated RSI,
  so a plain 'not overbought' cap would veto every real setup.
- MACD(12, 26, 9) — require MACD line above signal line (bullish)
- SMA(20) — require price above it (uptrend)
- Bollinger Bands(20, 2σ) — veto "squeeze" chop below 6% bandwidth
- A candidate that passes all 5 Pillars still gets vetoed if any filter
  fails — but only when ≥35 bars of price history exist. Without enough
  history the bot trades on the Pillars alone (logged, not silent).

**strategy.py** — Candidate carries optional price history (`closes`) and
the indicator checks run inside `gap_and_go_signal`. Vetoes are logged with
the failing filter names.

**risk_manager.py** — automatic stop-loss / take-profit validation per trade:
`validate_signal()` checks stop < entry < target, reward:risk ≥ 2:1, and
planned risk ≤ $50. `position_size()` is now the canonical $50-rule sizer.
All existing hard rules (daily −$100 halt, 3 consecutive losses, per-trade
$50 max) are untouched.

**config.py** — all indicator thresholds in one tunable section (IND_*).

**data_feed.py** — SimulationFeed demo candidates now carry synthetic price
history so the confirmation path exercises in simulation.

## Methods it draws from
- **Ross Cameron** — momentum + news catalysts: the 5 Pillars already encode
  this (gap %, relative volume, real news); indicators add the momentum
  confirmation (RSI/MACD).
- **Steven Dux** — systematic, risk-management-first: the automatic
  stop-loss/take-profit validation and hard halts.
- **Timothy Sykes** — pattern recognition and education: the journaled,
  logged, reviewable session structure (logs/ + "journal what happened").

## Future work (NOT implemented)
- **Machine learning** — no ML dependencies added (money is tight; nothing
  to install, nothing to pay for). Would need a training/validation loop
  over logged trades first.
- **News sentiment analysis** — no news API keys. Pillar 3 (news catalyst)
  is still a human-supplied/verifiable field; rumor spikes fail closed.

## Hard constraints (non-negotiable, unchanged)
- Paper endpoints only. The executor hard-codes
  `https://paper-api.alpaca.markets` and refuses anything else.
- MODE stays `alpaca_paper`. No live code paths exist.
- $50 max risk per trade, −$100 daily halt, 3 consecutive losses = done.
- No API keys in code — keys come from environment variables only.
