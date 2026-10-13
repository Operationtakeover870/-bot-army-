# Bot Army

Antonio's AI bot army. One bot, one objective each — specialists, not generalists.

## The bots

**Bot #1 — Trading Bot** (`trading-bot/`)
Paper-trading bot built on the 5 Pillars day-trading framework. Scans pre-market gappers, filters them through the 5 Pillars, plans Gap-and-Go entries with stop-loss and 2:1 profit targets, and enforces hard risk rules ($50 max risk per trade, -$100 daily max loss, halt after 3 straight losers). Paper trading only — it cannot place real-money orders.

**Bot #2 — Mix & Master Bot** (`mix-master/`)
Feed it a finished song mix (bounce/export from BandLab, FL Studio, wherever) and it runs a professional mastering chain: sub-bass cleanup, glue compression, stereo widening, safety limiting, and two-pass loudness normalization to -14 LUFS (the Spotify/YouTube standard). You get back the mastered track plus a plain-words report of what it did. Mastering only — it polishes a finished mix, it doesn't mix individual tracks.

## Doctrine

See `DOCTRINE.md` for the rules every bot follows: one bot = one objective, guardrails, logging, and nothing real moves without Antonio's explicit say-so each time.
