"""Order execution — swappable modules. PAPER TRADING ONLY.

- AlpacaPaperExecutor: sends real orders to Alpaca's PAPER api only.
  It refuses to run against any other base URL. Bracket orders
  (entry + stop-loss + take-profit) are placed as one unit.
- SimulationExecutor: pretends. Fills bracket orders against a
  synthetic intraday price path and reports which leg filled first.

Both expose the same interface, so the bot never knows which one
is behind it.
"""

from __future__ import annotations

import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import requests

import config
from strategy import Signal


@dataclass
class FillResult:
    symbol: str
    shares: int
    entry_price: float
    exit_price: float
    exit_reason: str  # "target" | "stop" | "expired"
    pnl: float        # dollars made (+) or lost (-)


class OrderExecutor(ABC):
    @abstractmethod
    def place_bracket(self, signal: Signal) -> FillResult:
        """Enter at signal.entry; exit at target (win) or stop (loss)."""
        ...


class AlpacaPaperExecutor(OrderExecutor):
    """Real orders against Alpaca PAPER trading only.

    SAFETY: the base URL is hard-coded to the paper endpoint and
    re-checked on every order. There is no live mode in this codebase.
    """

    PAPER_ONLY_URL = "https://paper-api.alpaca.markets"

    def __init__(self):
        self.api_key = os.environ.get("ALPACA_API_KEY", "")
        self.api_secret = os.environ.get("ALPACA_API_SECRET", "")
        if not self.api_key or not self.api_secret:
            raise RuntimeError(
                "AlpacaPaperExecutor needs ALPACA_API_KEY and "
                "ALPACA_API_SECRET environment variables."
            )
        if config.PAPER_API_BASE_URL != self.PAPER_ONLY_URL:
            raise RuntimeError(
                "REFUSED: config points away from the paper API. "
                "This bot is paper-only."
            )
        self.base = self.PAPER_ONLY_URL
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

    def place_bracket(self, signal: Signal) -> FillResult:
        if self.base != self.PAPER_ONLY_URL:  # belt and suspenders
            raise RuntimeError("REFUSED: not the paper trading endpoint.")
        order = {
            "symbol": signal.symbol,
            "qty": signal.shares,
            "side": "buy",
            "type": "market",
            "time_in_force": "day",
            "order_class": "bracket",
            "take_profit": {"limit_price": round(signal.target, 2)},
            "stop_loss": {"stop_price": round(signal.stop, 2)},
        }
        r = requests.post(f"{self.base}/v2/orders", headers=self.headers,
                          json=order, timeout=15)
        r.raise_for_status()
        # Paper fills are managed by Alpaca; for the bot's bookkeeping we
        # record the planned bracket. Actual fill prices come from the
        # paper account's order history (out of scope for this build).
        return FillResult(
            symbol=signal.symbol,
            shares=signal.shares,
            entry_price=signal.entry,
            exit_price=signal.entry,  # unknown until Alpaca reports; P&L reconciled later
            exit_reason="submitted-to-paper",
            pnl=0.0,
        )


class SimulationExecutor(OrderExecutor):
    """Simulated bracket fills on a synthetic intraday price path.

    The 'scenario' per symbol decides the shape of the path:
      win  -> price drifts up and tags the target
      loss -> price fades and tags the stop
      chop -> price wanders and exits flat-ish at a time stop
    This is for testing plumbing and risk rules, NOT for judging whether
    the strategy is profitable.
    """

    def __init__(self, scenarios: dict[str, str] | None = None, seed: int = 42):
        # NOTE: keep the caller's dict object (don't use `or {}`), because
        # the feed may populate it after we're constructed.
        self.scenarios = scenarios if scenarios is not None else {}
        self.rng = random.Random(seed)

    def _path(self, signal: Signal, scenario: str) -> list[float]:
        entry, stop, target = signal.entry, signal.stop, signal.target
        risk_d = entry - stop
        bars: list[float] = []
        if scenario == "win":
            # drift up and tag the target (small overshoot guarantees the tag)
            steps = self.rng.randint(15, 40)
            for i in range(60):
                frac = min(1.0, (i + 1) / steps)
                base = entry + (target - entry + 0.02) * frac
                price = base + self.rng.uniform(-0.25, 0.25) * risk_d
                bars.append(round(price, 2))
                if price >= target or price <= stop:
                    break
        elif scenario == "loss":
            # fade and tag the stop
            steps = self.rng.randint(10, 30)
            for i in range(60):
                frac = min(1.0, (i + 1) / steps)
                base = entry - (entry - stop + 0.02) * frac
                price = base + self.rng.uniform(-0.25, 0.25) * risk_d
                bars.append(round(price, 2))
                if price >= target or price <= stop:
                    break
        else:  # chop: wander, usually expires flat-ish
            price = entry
            for _ in range(60):
                price += self.rng.uniform(-0.3, 0.3) * risk_d
                price = round(price, 2)
                bars.append(price)
                if price >= target or price <= stop:
                    break
        return bars

    def place_bracket(self, signal: Signal) -> FillResult:
        scenario = self.scenarios.get(signal.symbol, "chop")
        exit_price, reason = signal.entry, "expired"
        for price in self._path(signal, scenario):
            if price >= signal.target:
                exit_price, reason = signal.target, "target"
                break
            if price <= signal.stop:
                exit_price, reason = signal.stop, "stop"
                break
        else:
            # time stop: flat-ish exit at the last simulated price
            reason = "expired"
        pnl = round((exit_price - signal.entry) * signal.shares, 2)
        return FillResult(
            symbol=signal.symbol,
            shares=signal.shares,
            entry_price=signal.entry,
            exit_price=exit_price,
            exit_reason=reason,
            pnl=pnl,
        )
