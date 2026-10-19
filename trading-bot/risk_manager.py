"""Risk manager: hard, mechanical rules. No overrides, no exceptions.

From the study notes (Ch. 5):
  - Risk ~$50 per trade to make ~$100 (2:1 reward-to-risk).
  - Daily max loss -$100 -> done for the day.
  - 3 losing trades in a row -> done for the day.

From the Day Trading Overview study material:
  - Automatic stop-loss / take-profit levels on every trade.
  - Position sizing tied to the max-risk rule.

When any limit hits, the bot stops trading for the day and logs why.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import config


@dataclass
class RiskManager:
    max_risk_per_trade: float = config.MAX_RISK_PER_TRADE
    profit_target: float = config.PROFIT_TARGET_PER_TRADE
    daily_max_loss: float = config.DAILY_MAX_LOSS
    max_consecutive_losses: int = config.MAX_CONSECUTIVE_LOSSES

    day_pnl: float = 0.0
    consecutive_losses: int = 0
    trades_today: int = 0
    halted: bool = False
    halt_reason: str = ""

    def _halt(self, reason: str) -> None:
        self.halted = True
        self.halt_reason = reason

    def can_open_trade(self, planned_risk: float) -> tuple[bool, str]:
        """Check whether a new trade is allowed right now."""
        if self.halted:
            return False, f"trading halted: {self.halt_reason}"
        if planned_risk > self.max_risk_per_trade:
            return (
                False,
                f"planned risk ${planned_risk:.2f} exceeds "
                f"${self.max_risk_per_trade:.2f} max per trade — skipped",
            )
        return True, "ok"

    def register_close(self, pnl: float) -> str:
        """Record a finished trade. Returns '' or a halt message."""
        self.trades_today += 1
        self.day_pnl += pnl
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        if self.day_pnl <= self.daily_max_loss:
            self._halt(
                f"daily max loss hit (P&L ${self.day_pnl:.2f} <= "
                f"${self.daily_max_loss:.2f}). Done for the day."
            )
            return f"HALT: {self.halt_reason}"
        if self.consecutive_losses >= self.max_consecutive_losses:
            self._halt(
                f"{self.consecutive_losses} losing trades in a row. "
                "Done for the day."
            )
            return f"HALT: {self.halt_reason}"
        return ""

    def position_size(self, entry: float, stop: float) -> tuple[int, float]:
        """Canonical sizer: shares = floor(max_risk / (entry - stop)).

        Planned risk can never exceed max_risk_per_trade. Minimum 1 share.
        Returns (shares, planned_risk_dollars).
        """
        risk_per_share = entry - stop
        if risk_per_share <= 0:
            return 0, 0.0
        shares = int(self.max_risk_per_trade // risk_per_share)
        shares = max(shares, 1)
        return shares, round(shares * risk_per_share, 2)

    def validate_signal(self, entry: float, stop: float, target: float,
                        planned_risk: float) -> tuple[bool, list[str]]:
        """Pre-trade structural checks on a planned bracket.

        Verifies the automatic stop-loss / take-profit levels make sense:
        stop below entry, target above entry, reward:risk >= 2:1, and
        planned risk within the per-trade maximum.
        Returns (ok, [reasons]) — reasons is empty when ok.
        """
        reasons: list[str] = []
        if not stop < entry:
            reasons.append(
                f"stop ${stop:.2f} must be below entry ${entry:.2f}")
        if not target > entry:
            reasons.append(
                f"target ${target:.2f} must be above entry ${entry:.2f}")
        if stop < entry:
            reward_risk = (target - entry) / (entry - stop)
            if round(reward_risk, 4) < 2.0:  # rounded: float dust ignored
                reasons.append(
                    f"reward:risk {reward_risk:.2f} below 2:1 minimum")
        if planned_risk > self.max_risk_per_trade + 1e-9:
            reasons.append(
                f"planned risk ${planned_risk:.2f} exceeds "
                f"${self.max_risk_per_trade:.2f} max per trade")
        return (len(reasons) == 0), reasons

    def summary(self) -> str:
        return (
            f"trades={self.trades_today} day_pnl=${self.day_pnl:.2f} "
            f"consecutive_losses={self.consecutive_losses} "
            f"halted={self.halted}"
            + (f" ({self.halt_reason})" if self.halted else "")
        )
