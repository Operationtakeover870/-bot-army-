"""Technical indicator confirmation filters — Day Trading Overview study material.

The 5 Pillars remain the PRIMARY gate. These indicators are CONFIRMATION
filters only: a candidate that passes all 5 Pillars gets its entry
confirmed (or vetoed) by momentum / trend / volatility checks before a
Gap-and-Go signal is built.

Pure standard library — no new dependencies (money is tight; nothing
to install).

Conventions:
- `closes`: list of closing prices, oldest -> newest.
- Every function returns None when there isn't enough data (fail-closed:
  the caller treats "no reading" as "no confirmation").
- All thresholds live in config.py (IND_*).
"""

from __future__ import annotations

from dataclasses import dataclass

import config


def sma(values: list[float], period: int) -> float | None:
    """Simple moving average of the last `period` values."""
    if len(values) < period or period <= 0:
        return None
    return sum(values[-period:]) / period


def _ema(values: list[float], period: int) -> list[float] | None:
    """Full EMA series, seeded with the SMA of the first `period` values."""
    if len(values) < period or period <= 0:
        return None
    k = 2 / (period + 1)
    ema_vals = [sum(values[:period]) / period]
    for v in values[period:]:
        ema_vals.append(v * k + ema_vals[-1] * (1 - k))
    return ema_vals


def rsi(closes: list[float], period: int = config.IND_RSI_PERIOD) -> float | None:
    """Wilder's RSI (0-100). None when there isn't enough data."""
    if len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(closes: list[float], fast: int = config.IND_MACD_FAST,
         slow: int = config.IND_MACD_SLOW,
         signal: int = config.IND_MACD_SIGNAL) -> tuple[float, float] | None:
    """MACD for the latest bar. Returns (macd_line, signal_line) or None."""
    if len(closes) < slow + signal:
        return None
    fast_ema = _ema(closes, fast)
    slow_ema = _ema(closes, slow)
    assert fast_ema is not None and slow_ema is not None
    offset = len(fast_ema) - len(slow_ema)
    macd_line = [f - s for f, s in zip(fast_ema[offset:], slow_ema)]
    signal_ema = _ema(macd_line, signal)
    if signal_ema is None:
        return None
    return macd_line[-1], signal_ema[-1]


def bollinger(closes: list[float], period: int = config.IND_BB_PERIOD,
              std: float = config.IND_BB_STD) -> tuple[float, float, float] | None:
    """Bollinger Bands for the latest bar. Returns (lower, middle, upper)."""
    if len(closes) < period:
        return None
    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((x - middle) ** 2 for x in window) / period
    sd = variance ** 0.5
    return middle - std * sd, middle, middle + std * sd


@dataclass
class IndicatorCheck:
    name: str
    passed: bool
    detail: str


def confirm_entry(closes: list[float]) -> list[IndicatorCheck]:
    """Run every confirmation filter. Use all_confirmed() on the result."""
    checks: list[IndicatorCheck] = []
    price = closes[-1] if closes else float("nan")

    r = rsi(closes)
    rsi_ok = (r is not None
              and config.IND_RSI_MIN <= r <= config.IND_RSI_MAX)
    checks.append(IndicatorCheck(
        f"RSI(14) in momentum zone "
        f"({config.IND_RSI_MIN:.0f}-{config.IND_RSI_MAX:.0f})",
        rsi_ok,
        f"RSI {r:.1f}" if r is not None else "RSI: insufficient data",
    ))

    m = macd(closes)
    checks.append(IndicatorCheck(
        "MACD bullish (line > signal)",
        m is not None and m[0] > m[1],
        f"MACD {m[0]:.4f} vs signal {m[1]:.4f}"
        if m is not None else "MACD: insufficient data",
    ))

    s = sma(closes, config.IND_SMA_PERIOD)
    checks.append(IndicatorCheck(
        f"Price above SMA({config.IND_SMA_PERIOD})",
        s is not None and price > s,
        f"price {price:.2f} vs SMA {s:.2f}"
        if s is not None else "SMA: insufficient data",
    ))

    bb = bollinger(closes)
    if bb is None:
        checks.append(IndicatorCheck(
            "Bollinger: no squeeze", False, "Bollinger: insufficient data"))
    else:
        lower, middle, upper = bb
        bandwidth = (upper - lower) / middle if middle else 0.0
        checks.append(IndicatorCheck(
            "Bollinger: no squeeze",
            bandwidth >= config.IND_BB_MIN_BANDWIDTH,
            f"bandwidth {bandwidth:.1%} "
            f"(veto below {config.IND_BB_MIN_BANDWIDTH:.0%})",
        ))

    return checks


def all_confirmed(checks: list[IndicatorCheck]) -> bool:
    """True only if every confirmation filter passed."""
    return all(c.passed for c in checks)
