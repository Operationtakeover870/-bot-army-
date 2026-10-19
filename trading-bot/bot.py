"""5-Pillars paper trading bot — main session runner.

One run = one simulated (or Alpaca paper) morning session:
  1. Scan pre-market candidates.
  2. Filter through the 5 Pillars (fail-closed).
  3. Build Gap-and-Go plans for survivors (with indicator confirmation
     when price history is available).
  4. Risk-manager gate on every trade (hard rules + signal validation).
  5. Execute via the configured executor (simulation by default).
  6. Log everything; halt for the day when a hard rule trips.

Usage:
    python3 bot.py                      # simulation mode, demo candidates
    python3 bot.py --watchlist file.json # simulation mode, your candidates
    python3 bot.py --mode alpaca --watchlist SYM1 SYM2
                                        # Alpaca paper (needs API keys in env)

PAPER TRADING ONLY. Nothing here can place a real-money order.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from data_feed import AlpacaFeed, SimulationFeed
from logger import DailyLogger
from order_executor import AlpacaPaperExecutor, SimulationExecutor
from risk_manager import RiskManager
from strategy import check_five_pillars, gap_and_go_signal, passes_all


def run_session(mode: str, watchlist: list[str] | None,
               watchlist_file: str | None, log: DailyLogger) -> None:
    log.section(f"SESSION START — mode={mode} (PAPER ONLY, no real money)")

    # --- Build the swappable pieces ---
    if mode == "alpaca":
        feed = AlpacaFeed(watchlist=watchlist or [])
        executor = AlpacaPaperExecutor()
        scenarios: dict[str, str] = {}
    else:
        log.log("SIMULATION MODE — every price and fill is invented. "
                "Nothing here touches a market.")
        feed = SimulationFeed(watchlist_file=watchlist_file)
        scenarios = feed.scenarios
        executor = SimulationExecutor(scenarios=scenarios)

    risk = RiskManager()

    # --- 1. Scan ---
    log.section("PRE-MARKET SCAN")
    candidates = feed.get_premarket_candidates()
    log.log(f"scanner found {len(candidates)} gapping candidate(s)")
    for c in candidates:
        log.log(f"  {c.symbol}: ${c.price:.2f} ({c.day_gain_pct:+.1f}%), "
                f"rel vol {c.relative_volume:.1f}x, "
                f"pre-market shares {c.premarket_shares:,.0f}")

    # --- 2. Five Pillars filter ---
    log.section("5-PILLARS FILTER")
    survivors = []
    for c in candidates:
        results = check_five_pillars(c)
        ok = passes_all(results)
        log.log(f"{c.symbol}: {'PASS' if ok else 'FAIL'}")
        for r in results:
            log.log(f"    [{ 'x' if r.passed else ' ' }] {r.pillar}: {r.detail}")
        if ok:
            survivors.append(c)
    log.log(f"{len(survivors)} of {len(candidates)} passed all 5 Pillars")

    # --- 3-5. Signals -> risk gate -> execution ---
    log.section("TRADING")
    for c in survivors:
        if risk.halted:
            log.log(f"halted ({risk.halt_reason}) — skipping {c.symbol}")
            break
        signal = gap_and_go_signal(c)
        if signal is None:
            veto = ""
            if c.indicator_checks:
                failed = [chk.name for chk in c.indicator_checks
                          if not chk.passed]
                if failed:
                    veto = f" — indicator veto: {', '.join(failed)}"
            log.log(f"{c.symbol}: no clean Gap-and-Go setup{veto} — skipped")
            continue
        log.log(f"{c.symbol}: SIGNAL entry ${signal.entry:.2f} | "
                f"stop ${signal.stop:.2f} | target ${signal.target:.2f} | "
                f"{signal.shares} shares | planned risk ${signal.planned_risk:.2f}")

        allowed, why = risk.can_open_trade(signal.planned_risk)
        if not allowed:
            log.log(f"{c.symbol}: BLOCKED by risk manager — {why}")
            continue

        ok, reasons = risk.validate_signal(
            signal.entry, signal.stop, signal.target, signal.planned_risk)
        if not ok:
            log.log(f"{c.symbol}: BLOCKED by risk validation — "
                    f"{'; '.join(reasons)}")
            continue

        fill = executor.place_bracket(signal)
        log.log(f"{c.symbol}: exit {fill.exit_reason} @ ${fill.exit_price:.2f} "
                f"-> P&L ${fill.pnl:+.2f}")

        halt_msg = risk.register_close(fill.pnl)
        if halt_msg:
            log.log(halt_msg)

    # --- 6. Summary ---
    log.section("SESSION SUMMARY")
    log.log(risk.summary())
    log.log("Session complete. Review logs/ and journal what happened.")


def main() -> None:
    parser = argparse.ArgumentParser(description="5-Pillars paper trading bot")
    parser.add_argument("--mode", choices=["simulation", "alpaca"],
                        default=config.MODE,
                        help="simulation = fake data, no keys (default); "
                             "alpaca = Alpaca paper account (needs API keys)")
    parser.add_argument("--watchlist", nargs="*",
                        help="symbols for Alpaca mode, e.g. --watchlist AAPL TSLL")
    parser.add_argument("--watchlist-file",
                        help="JSON file of candidates for simulation mode")
    args = parser.parse_args()

    log = DailyLogger(log_dir=config.LOG_DIR)
    try:
        run_session(args.mode, args.watchlist, args.watchlist_file, log)
    except RuntimeError as e:
        log.log(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
