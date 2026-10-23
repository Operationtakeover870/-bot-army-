# Bot #4 — Clip Bot

The viral content machine of the bot army. Two jobs, one bot:

**Job A — Viral Scout.** Every morning it hunts for trending video content
worth posting or reacting to: funny clips, wild moments, trending memes,
skit-worthy scenes. Delivers a short digest: what it is, the link, why it's
blowing up right now, and an angle for Antonio's own post.

**Job B — Clipper.** Takes a long video and cuts it into vertical 9:16
shorts ready for TikTok, Reels, and Shorts.

One bot, one objective: keep Antonio's posting pipeline fed — find what's
hot, cut what's long.

## Run it — Clipper

Needs ffmpeg on PATH. No pip packages.

```bash
# Preview the auto-detected best moments (cuts nothing)
python3 clip.py longvideo.mp4 --suggest

# Auto-cut the 3 loudest moments into vertical shorts
python3 clip.py longvideo.mp4 --auto

# Cut exact ranges (timestamps like 2:14 or plain seconds)
python3 clip.py longvideo.mp4 --cut 2:14-2:40 --cut 5:00-5:30
```

Clips land in `clips/` as 720x1280 MP4s, ~15–45 seconds each, audio kept.

## How the auto-cut works

1. Reads the audio's momentary loudness (ebur128) across the whole video.
2. Finds peaks sitting well above the video's own baseline — laughs,
   reactions, exclamations, beat drops.
3. Cuts a ~30 second window around each peak, center-cropped to vertical 9:16.
4. No usable audio? Falls back to even splits so it never comes back empty.

## Run it — Scout

The scout is an agent runbook, not a script: `scout/SCOUT.md`. The morning
agent follows it — searches social + web for what's actually trending,
checks traction signals, and writes the digest in `scout/digest-template.md`
format. Proposed schedule: daily ~8:30 AM CT (before the 9:30 trading
keys nudge). Cron not created yet — Antonio confirms timing first.

## Limits

- Auto-cut finds *loud* moments, not *funny* moments. A quiet punchline can
  slip past it — that's what `--suggest` + your eyes are for.
- No captions in v1. Clips come out clean, ready for TikTok's auto-captions.
- Scout reports what it finds with links; it never downloads or re-uploads
  anyone's content. Angles lean toward react/duet/recreate, not straight repost.
- Free tier only: no paid APIs anywhere in this bot.

## Doctrine

Follows `DOCTRINE.md`: one objective, guardrails, visible trail instead of a
black box, and nothing real moves — this bot finds and cuts; Antonio decides
what gets posted.
