"""Daily timestamped logging for the trading bot.

Every scan result, signal, simulated order, and halt decision is written
to logs/YYYY-MM-DD.log and also printed to the screen.
"""

from __future__ import annotations

import os
from datetime import datetime, date


class DailyLogger:
    def __init__(self, log_dir: str = "logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.path = os.path.join(log_dir, f"{date.today().isoformat()}.log")
        # Mark the start of a new run inside the day's file.
        self._write("=" * 60)
        self._write(f"RUN STARTED {datetime.now().isoformat(timespec='seconds')}")

    def _write(self, line: str) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        print(line, flush=True)
        self._write(line)

    def section(self, title: str) -> None:
        self.log("-" * 50)
        self.log(title)
        self.log("-" * 50)
