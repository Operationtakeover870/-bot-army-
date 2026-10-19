"""Market data feed — swappable modules.

- AlpacaFeed: pulls real pre-market snapshots from Alpaca's data API.
  Needs ALPACA_API_KEY / ALPACA_API_SECRET. Read-only market data.
- SimulationFeed: generates clearly-labeled fake candidates so the bot
  can be tested with zero keys and zero network.

Both return the same Candidate objects, so the strategy code never
knows which feed is behind it.
"""

from __future__ import annotations

import json
import os
import random
from abc import ABC, abstractmethod

import requests

import config
from strategy import Candidate


class MarketDataFeed(ABC):
    @abstractmethod
    def get_premarket_candidates(self) -> list[Candidate]:
        """Return stocks gapping up in pre-market, newest data available."""
        ...


class AlpacaFeed(MarketDataFeed):
    """Real market data from Alpaca (paper/free tier).

    NOTE: Alpaca's free data has no built-in gap screener and no float
    field, so this feed checks a watchlist of symbols you supply and
    marks float as unknown (the 5-Pillars check fails closed on it —
    see README "Limitations"). Plug in a screener or fundamentals
    source later to fill those gaps.
    """

    def __init__(self, watchlist: list[str] | None = None):
        self.api_key = os.environ.get("ALPACA_API_KEY", "")
        self.api_secret = os.environ.get("ALPACA_API_SECRET", "")
        if not self.api_key or not self.api_secret:
            raise RuntimeError(
                "AlpacaFeed needs ALPACA_API_KEY and ALPACA_API_SECRET "
                "environment variables. Use simulation mode instead."
            )
        self.watchlist = watchlist or []
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{config.DATA_API_BASE_URL}/v2{path}"
        r = requests.get(url, headers=self.headers, params=params or {}, timeout=15)
        r.raise_for_status()
        return r.json()

    def get_premarket_candidates(self) -> list[Candidate]:
        candidates: list[Candidate] = []
        for symbol in self.watchlist:
            try:
                snap = self._get(f"/stocks/{symbol}/snapshot")
                daily = snap.get("dailyBar", {}) or {}
                prev_daily = snap.get("prevDailyBar", {}) or {}
                prev_close = float(prev_daily.get("c", 0) or 0)
                price = float(daily.get("c", 0) or 0)
                volume = float(daily.get("v", 0) or 0)
                if prev_close <= 0 or price <= 0:
                    continue
                day_gain_pct = (price - prev_close) / prev_close * 100
                premarket_shares = volume  # snapshot volume before open ~= pre-market
                if (
                    day_gain_pct >= config.PREMARKET_MIN_GAP_PCT
                    and premarket_shares >= config.PREMARKET_MIN_SHARES
                ):
                    candidates.append(Candidate(
                        symbol=symbol,
                        price=price,
                        prev_close=prev_close,
                        day_gain_pct=day_gain_pct,
                        relative_volume=0.0,  # needs average-volume history; unknown here
                        premarket_shares=premarket_shares,
                        float_shares=None,   # not in free Alpaca data; fails closed
                        news_catalyst="",
                        premarket_high=float(daily.get("h", price) or price),
                        premarket_low=float(daily.get("l", price) or price),
                    ))
            except Exception as e:  # one bad symbol must not kill the scan
                print(f"[feed] skipping {symbol}: {e}")
        return candidates


class SimulationFeed(MarketDataFeed):
    """Fake pre-market data for testing. Every value is invented.

    Loads candidates from a JSON watchlist file when given, otherwise
    generates a small deterministic demo set (seeded, so runs repeat).
    Each candidate carries a 'scenario' used by the simulator to decide
    whether the trade wins or loses: 'win', 'loss', or 'chop'.
    """

    def __init__(self, watchlist_file: str | None = None,
                 seed: int = config.SIM_RANDOM_SEED):
        self.watchlist_file = watchlist_file
        self.rng = random.Random(seed)
        self.scenarios: dict[str, str] = {}

    def _synthetic_closes(self, prev_close: float, price: float) -> list[float]:
        """Fake pre-market price history (oldest -> newest) for indicator
        confirmation in simulation. 28 bars of chop around the previous
        close, then a 12-bar staircase climb (up bars with pullbacks) into
        the current price — every value invented, like the rest of the demo.
        """
        closes: list[float] = []
        p = prev_close
        for _ in range(28):
            p *= 1 + self.rng.uniform(-0.02, 0.02)
            closes.append(round(max(p, 0.01), 2))
        start = closes[-1]
        total = price - start
        steps = [0.013, 0.009, -0.004] * 4
        denom = start * sum(steps)
        scale = total / denom if denom else 0.0
        for s in steps:
            p = closes[-1] * (1 + s * scale)
            closes.append(round(max(p, 0.01), 2))
        closes[-1] = price
        return closes

    def _demo_candidates(self) -> list[Candidate]:
        demo = [
            # (symbol, prev_close, gap_pct, rel_vol, float_M, catalyst, scenario)
            ("DEMO", 5.00, 18.0, 7.2, 6.5, "beats earnings, raises guidance", "win"),
            ("FAKE", 8.00, 12.5, 6.1, 8.2, "FDA approval announced", "loss"),
            ("TEST", 3.00, 22.0, 9.4, 4.1, "major partnership deal", "win"),
            ("RUMR", 6.00, 15.0, 5.5, 9.0, "", "chop"),  # no catalyst -> filtered out
            ("BIGF", 4.00, 11.0, 5.8, 45.0, "analyst upgrade", "loss"),  # float too big
        ]
        out = []
        for sym, prev, gap, rvol, float_m, news, scen in demo:
            price = round(prev * (1 + gap / 100), 2)
            pm_high = round(price * 1.01, 2)
            pm_low = round(price * 0.985, 2)
            self.scenarios[sym] = scen
            out.append(Candidate(
                symbol=sym,
                price=price,
                prev_close=prev,
                day_gain_pct=gap,
                relative_volume=rvol,
                premarket_shares=self.rng.randint(150_000, 900_000),
                float_shares=float_m * 1_000_000,
                news_catalyst=news,
                premarket_high=pm_high,
                premarket_low=pm_low,
                closes=self._synthetic_closes(prev, price),
            ))
        return out

    def _file_candidates(self) -> list[Candidate]:
        with open(self.watchlist_file, encoding="utf-8") as f:
            raw = json.load(f)
        out = []
        for item in raw:
            self.scenarios[item["symbol"]] = item.get("scenario", "chop")
            out.append(Candidate(
                symbol=item["symbol"],
                price=float(item["price"]),
                prev_close=float(item["prev_close"]),
                day_gain_pct=float(item["day_gain_pct"]),
                relative_volume=float(item["relative_volume"]),
                premarket_shares=float(item["premarket_shares"]),
                float_shares=float(item["float_shares"])
                if item.get("float_shares") else None,
                news_catalyst=item.get("news_catalyst", ""),
                premarket_high=float(item.get("premarket_high", item["price"])),
                premarket_low=float(item.get("premarket_low", item["price"])),
            ))
        return out

    def get_premarket_candidates(self) -> list[Candidate]:
        if self.watchlist_file:
            return self._file_candidates()
        return self._demo_candidates()

    def scenario_for(self, symbol: str) -> str:
        return self.scenarios.get(symbol, "chop")
