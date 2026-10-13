"""Risk manager: hard, mechanical rules. No overrides, no exceptions.

From the study notes (Ch. 5):
  - Risk ~$50 per trade to make ~$100 (2:1 reward-to-risk).
  - Daily max loss -$100 -> done for the day.
  - 3 losing trades in a row -> done for the day.

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

    def summary(self) -> str:
        return (
            f"trades={self.trades_today} day_pnl=${self.day_pnl:.2f} "
            f"consecutive_losses={self.consecutive_losses} "
            f"halted={self.halted}"
            + (f" ({self.halt_reason})" if self.halted else "")
        )
