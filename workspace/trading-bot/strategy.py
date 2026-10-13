"""Strategy module: the 5 Pillars filter + Gap-and-Go entries.

From the study notes (Ch. 6 and Ch. 10):

THE 5 PILLARS — a stock must pass ALL five to be a trade candidate:
  1. Relative volume >= 5x average
  2. Up >= 10% on the day
  3. Real, verifiable news catalyst (earnings, FDA, partnership...)
  4. Price between $2 and $20
  5. Float under ~10M shares

GAP AND GO ENTRY:
  - Stock gapped up pre-market on news and passes the 5 Pillars.
  - Buy the break above the pre-market high (or the first 1-minute
    candle's high) with the stop at the low of that candle.
  - Profit target = entry + 2 * (entry - stop)  -> 2:1 reward-to-risk.
  - Position size: shares = $50 max risk / (entry - stop).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import config


@dataclass
class Candidate:
    """One stock the pre-market scanner found."""
    symbol: str
    price: float                 # current / pre-market price
    prev_close: float            # previous day's close
    day_gain_pct: float          # (price - prev_close) / prev_close * 100
    relative_volume: float       # today's volume vs. average
    premarket_shares: float      # shares traded pre-market
    float_shares: float | None   # shares available to trade (None = unknown)
    news_catalyst: str = ""      # description of the news, "" = none found
    premarket_high: float = 0.0
    premarket_low: float = 0.0


@dataclass
class PillarResult:
    pillar: str
    passed: bool
    detail: str


def check_five_pillars(c: Candidate) -> list[PillarResult]:
    """Run a candidate through all 5 Pillars. Fail-closed: unknown = fail."""
    results = []

    results.append(PillarResult(
        "1. Relative volume >= 5x",
        c.relative_volume >= config.MIN_RELATIVE_VOLUME,
        f"relative volume {c.relative_volume:.1f}x "
        f"(needs >= {config.MIN_RELATIVE_VOLUME}x)",
    ))

    results.append(PillarResult(
        "2. Up >= 10% on the day",
        c.day_gain_pct >= config.MIN_DAY_GAIN_PCT,
        f"up {c.day_gain_pct:.1f}% (needs >= {config.MIN_DAY_GAIN_PCT}%)",
    ))

    has_catalyst = bool(c.news_catalyst.strip()) if config.REQUIRE_NEWS_CATALYST else True
    results.append(PillarResult(
        "3. Real news catalyst",
        has_catalyst,
        f"catalyst: {c.news_catalyst or 'NONE FOUND — rumor spikes are skipped'}",
    ))

    results.append(PillarResult(
        "4. Price $2-$20",
        config.MIN_PRICE <= c.price <= config.MAX_PRICE,
        f"price ${c.price:.2f} (needs ${config.MIN_PRICE:.0f}-${config.MAX_PRICE:.0f})",
    ))

    float_ok = c.float_shares is not None and c.float_shares <= config.MAX_FLOAT_SHARES
    results.append(PillarResult(
        "5. Float under ~10M",
        float_ok,
        f"float {c.float_shares / 1e6:.1f}M" if c.float_shares
        else "float UNKNOWN — failed closed (no trade without it)",
    ))

    return results


def passes_all(results: list[PillarResult]) -> bool:
    return all(r.passed for r in results)


@dataclass
class Signal:
    """A Gap-and-Go trade plan: entry, stop, and target decided BEFORE entry."""
    symbol: str
    entry: float
    stop: float
    target: float
    shares: int
    planned_risk: float  # dollars actually risked (shares * (entry - stop))


def position_size(entry: float, stop: float,
                  max_risk: float = config.MAX_RISK_PER_TRADE) -> tuple[int, float]:
    """shares = max dollars willing to lose / (entry - stop)."""
    risk_per_share = entry - stop
    if risk_per_share <= 0:
        return 0, 0.0
    shares = int(max_risk // risk_per_share)
    shares = max(shares, 1)
    return shares, round(shares * risk_per_share, 2)


def gap_and_go_signal(c: Candidate) -> Signal | None:
    """Build the Gap-and-Go plan: buy the break of the pre-market high.

    Entry = pre-market high. Stop = pre-market low (the breakout candle's
    low — if price falls back under it, the breakout failed).
    Target = entry + 2 * risk distance (2:1 reward-to-risk).
    """
    if c.premarket_high <= 0 or c.premarket_low <= 0:
        return None
    entry = round(c.premarket_high, 2)
    stop = round(c.premarket_low, 2)
    if entry <= stop:
        return None
    risk_distance = entry - stop
    target = round(entry + 2 * risk_distance, 2)
    shares, planned_risk = position_size(entry, stop)
    if shares <= 0:
        return None
    return Signal(
        symbol=c.symbol,
        entry=entry,
        stop=stop,
        target=target,
        shares=shares,
        planned_risk=planned_risk,
    )
