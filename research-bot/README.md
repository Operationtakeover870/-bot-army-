# Bot #3 — Brains

The research brain of the bot army. Ask it anything — it searches the open
web across multiple angles, reads the top results, and reports back with
cited sources.

One bot, one objective: answer the question with evidence, or say plainly
that it couldn't.

## Run it

```bash
pip install -r requirements.txt
python3 bot.py "your question"
```

Example:

```bash
python3 bot.py "what is the 5 pillars trading strategy"
```

## How it works

1. Turns your question into up to 4 search angles (the question itself,
   keyword form, "what is …" form, "… explained").
2. Queries keyless sources: the Wikipedia API (opensearch + extracts) and
   DuckDuckGo's Instant Answer API.
3. Reads the top articles and prints a findings digest with numbered
   sources, plus a research trail (angles tried, articles read) so you can
   check its work.

## Limits

- Keyless sources only — no Google/Bing APIs, no paywalled content.
  (DuckDuckGo's HTML search blocks bots, so Brains uses their keyless
  JSON instant-answer endpoint instead.)
- Extractive, not a language model: it reports what sources say, it doesn't
  opine. When sources disagree, it shows the disagreement.
- Read-only: it never posts, sends, or changes anything.
- If the network is down it says so and exits — no fake answers.

## Doctrine

Follows `DOCTRINE.md`: one objective, guardrails, visible research trail
instead of a black box, and nothing real moves — this bot only reads.
