# Bot Army — Doctrine (DRAFT for Antonio's reaction)

Antonio's rule: **one bot, one objective.** Specialists, not generalists.
Everything handled correctly and perfectly.

## Rules every bot follows

1. One bot = one objective. If a bot needs a second job, that's a second bot.
2. The objective gets written down before the bot is built — what it does, and what it never does.
3. Every bot has guardrails: what it's allowed to touch, and a stop condition.
4. Every bot logs what it did so it can be checked. No black boxes.
5. Nothing real moves without Antonio's explicit say-so each time — no money, no account changes, no messages sent as him.

## Bot #1 — Trading Bot (already built)

- **Objective:** run the pre-market scan and practice trades on real market data.
- **Status:** built and tested in simulation with fake data. Next step is hooking it to Alpaca paper trading once Antonio creates a free Alpaca account — his move, no rush.
- **Its rules:** 5 Pillars filter, Gap-and-Go entries, max $50 risk per trade, $100 target, stops for the day at -$100 or 3 straight losses.
- **Deploy path is open:** the GitHub connector is now authenticated to Antonio's account (repos `Operationtakeover870/brain-backend` and `Operationtakeover870/playing-da-field`). The bot stays local until he says push.

## Candidate Bot #2 — Watchlist Scout

- **Objective:** the pre-market watchlist routine from this morning, as a standing specialist — scan real pre-market gainers against the 5 Pillars, deliver entry/stop/target by 8:00 AM CT.
- **Status:** proven once (today, 2 setups + 1 watch-only). Needs Antonio's go-ahead to run again — one-off, not automatic.

## Candidate Bot #3 — Bonus Watcher

- **Objective:** watch his casino/sportsbook apps for expiring bonuses and deadlines, and flag them in time to act. (Example: Kalshi's $25 bonus expired at midnight last night; McLuck ticket #4010217.)
- **Status:** idea only.

## Spec template (every new bot gets one of these)

- Name:
- One objective (one sentence):
- Inputs: / Outputs:
- Tools it's allowed to use:
- Success check (how we know it worked):
- Guardrails (what it never does):
- Stop condition:

## Open questions for Antonio

1. Bot #2 next, or a different objective first?
2. The bots need call signs — what should we name them?
3. Anything in this doctrine you'd change?
