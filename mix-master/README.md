# Mix & Master Bot (Bot #2)

This bot takes your finished song mix and makes it sound polished and
loud enough for streaming — like what a mastering engineer does, but
automatic. It does **not** touch real money, accounts, or anything else.
One bot, one job: mastering.

## What it does

You give it your mix (the bounce/export from BandLab, FL Studio, wherever).
It:

1. **Listens first** — measures how loud your mix actually is.
2. **Cleans it up** — cuts low rumble you can't hear, gently evens out
   the levels so everything sits together, widens the stereo a touch.
3. **Caps it** — makes sure nothing can clip or distort.
4. **Sets the loudness** — brings it to -14 LUFS, the level Spotify and
   YouTube expect. Not guessed — calculated from the actual measurement.

You get back two files: the mastered song, and a short report that says
what it did in plain words.

## How to use it

```bash
cd ~/workspace/bot-army/mix-master

# Basic: feed it your mix, get back song_mastered.wav + a report
python3 master.py mysong.wav

# Name your own output file
python3 master.py mysong.wav -o mysong_MASTERED.wav

# MP3 in, MP3 out
python3 master.py mysong.mp3 -o mysong_MASTERED.mp3

# Pick a different loudness target (default is -14)
python3 master.py mysong.wav --target -14
```

Nothing to install — it only needs FFmpeg, which is already on the machine.

## What it does NOT do (yet)

- **Mixing individual tracks** (vocals, drums, bass separately) — right
  now it masters your finished stereo mix only. The door is open for stem
  mixing later (see `stems.py`).
- **Creative choices** — it won't pick your reverb, decide your vocal
  should be louder, or change your sound. It polishes what you made.

## Can it go inside my music app? (honest answer)

Researched October 2026 — here's what's real:

- **REAPER** — YES, this is the real path. It has an official scripting
  system (ReaScript) that lets outside programs control it: set levels,
  add effects, render mixes. If the bot ever lives *inside* a DAW, it'll
  be REAPER.
- **FL Studio** — no official way in. Its scripting only works for MIDI
  controllers (keyboards/pads), not for outside programs. There are
  unofficial hacks, but nothing reliable.
- **BandLab** — no public API at all. A bot cannot get inside BandLab.

So the honest setup: **you export your mix from whatever app you use,
feed the file to this bot, and it hands back the mastered version.**
That works with every app, today, no hacks needed. If you ever move to
REAPER on a computer, the bot can grow to drive it directly.

## Files

- `master.py` — the bot itself (run this)
- `config.py` — all the settings in one place (loudness target, etc.)
- `analyze.py` — measures your mix
- `chain.py` — the mastering chain (EQ → compression → width → limiter → loudness)
- `report.py` — writes the plain-words report
- `stems.py` — empty for now; this is where stem mixing will live later
- `requirements.txt` — nothing to install (standard library + FFmpeg only)
