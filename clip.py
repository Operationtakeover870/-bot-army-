#!/usr/bin/env python3
"""
Clip Bot — Bot #4 of the bot army.
Job B: turn a long video into vertical 9:16 shorts for TikTok/Reels/Shorts.

Two ways to pick the cuts:
  1. Auto:  python3 clip.py video.mp4 --auto
     Finds the loudest moments (laughs, reactions, exclamations) by reading
     the audio's momentary loudness and cuts a short around each peak.
  2. Manual: python3 clip.py video.mp4 --cut 2:14-2:40 --cut 5:00-5:30
     Cuts exactly the ranges you give. Timestamps can be 1:02:33 or plain seconds.

Preview first without cutting anything:
     python3 clip.py video.mp4 --suggest

Needs: ffmpeg + ffprobe on PATH. No pip packages. Everything is free.
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys

TARGET_LEN = 30      # seconds per auto clip
MIN_LEN = 15
MAX_LEN = 45
MIN_GAP = 20         # seconds between auto peaks
SPIKE_ABOVE_MEDIAN = 9.0  # loudness units above the median = a "moment"
OUT_W, OUT_H = 720, 1280  # vertical 9:16


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[:500])
    return p.stdout, p.stderr


def probe(path):
    out, _ = run(["ffprobe", "-v", "quiet", "-print_format", "json",
                  "-show_format", "-show_streams", path])
    return json.loads(out)


def duration_of(path):
    info = probe(path)
    dur = float(info["format"].get("duration", 0))
    if dur <= 0:
        for s in info["streams"]:
            if "duration" in s:
                dur = max(dur, float(s["duration"]))
    if dur <= 0:
        raise RuntimeError("Could not read video length.")
    return dur


def has_audio(path):
    info = probe(path)
    return any(s.get("codec_type") == "audio" for s in info["streams"])


def loudness_series(path):
    """Per-moment loudness (t, LUFS-ish) via ebur128. Returns list of (t, m)."""
    # NOTE: do NOT use framelog=quiet here — in ffmpeg 8.x it suppresses the
    # per-frame lines entirely. Default (info level) prints "t: … M: …" lines.
    _, err = run(["ffmpeg", "-hide_banner", "-i", path,
                  "-map", "0:a", "-af", "ebur128=peak=true",
                  "-f", "null", "-"])
    series = []
    for line in err.splitlines():
        m = re.search(r"t:\s*([\d.]+).*?M:\s*(-?[\d.]+)", line)
        if m:
            t, loud = float(m.group(1)), float(m.group(2))
            if loud > -70:  # ignore digital silence
                series.append((t, loud))
    return series


def find_peaks(series, dur, top_n):
    if len(series) < 10:
        return []
    median = statistics.median(v for _, v in series)
    thresh = median + SPIKE_ABOVE_MEDIAN
    # local maxima above threshold
    cands = []
    for i in range(1, len(series) - 1):
        t, v = series[i]
        if v >= thresh and v >= series[i - 1][1] and v >= series[i + 1][1]:
            cands.append((t, v))
    # strongest first, enforce spacing
    cands.sort(key=lambda x: -x[1])
    picked = []
    for t, v in cands:
        if all(abs(t - p[0]) >= MIN_GAP for p in picked):
            picked.append((t, v))
        if len(picked) >= top_n:
            break
    # windows centered on each peak, target length, clamped to video
    wins = []
    for t, v in sorted(picked):
        half = TARGET_LEN / 2
        start = max(0.0, t - half)
        end = min(dur, t + half)
        if end - start < MIN_LEN:
            continue
        if end - start > MAX_LEN:
            mid = (start + end) / 2
            start, end = mid - MAX_LEN / 2, mid + MAX_LEN / 2
        wins.append((start, end, v))
    # drop overlaps, keep the louder one
    wins.sort(key=lambda w: -w[2])
    final = []
    for w in wins:
        if all(w[1] <= f[0] or w[0] >= f[1] for f in final):
            final.append(w)
    return sorted(final)


def even_splits(dur, top_n):
    """Fallback when there is no usable audio: even chunks across the video."""
    n = max(1, min(top_n, int(dur // MIN_LEN)))
    chunk = dur / n
    wins = []
    for i in range(n):
        s = i * chunk
        e = min(dur, s + min(chunk, MAX_LEN))
        if e - s >= MIN_LEN:
            wins.append((s, e, 0.0))
    return wins


def parse_stamp(s):
    s = s.strip()
    if ":" in s:
        parts = [float(p) for p in s.split(":")]
        total = 0.0
        for p in parts:
            total = total * 60 + p
        return total
    return float(s)


def parse_range(s):
    if "-" not in s:
        raise ValueError(f"Bad range '{s}' — use like 2:14-2:40")
    a, b = s.split("-", 1)
    start, end = parse_stamp(a), parse_stamp(b)
    if end <= start:
        raise ValueError(f"Bad range '{s}' — end must be after start")
    return start, end


def fmt(t):
    m, s = divmod(int(round(t)), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def cut(path, start, end, out_path):
    vf = (f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,"
          f"crop={OUT_W}:{OUT_H}")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-ss", f"{start:.2f}", "-i", path, "-t", f"{end - start:.2f}",
         "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "23",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", out_path])


def main():
    ap = argparse.ArgumentParser(description="Clip Bot — long video to vertical shorts.")
    ap.add_argument("input", help="long video file")
    ap.add_argument("--out", default="clips", help="output folder (default: clips)")
    ap.add_argument("--suggest", action="store_true",
                    help="print suggested cuts, don't cut anything")
    ap.add_argument("--auto", action="store_true",
                    help="auto-find loud moments and cut them")
    ap.add_argument("--cut", action="append", default=[],
                    help="manual range like 2:14-2:40 (repeatable)")
    ap.add_argument("--top", type=int, default=3, help="max auto clips (default 3)")
    args = ap.parse_args()

    src = args.input
    if not os.path.isfile(src):
        sys.exit(f"Can't find that file: {src}")
    dur = duration_of(src)
    print(f"Video: {src} ({fmt(dur)} long)")

    jobs = []
    if args.cut:
        for r in args.cut:
            s, e = parse_range(r)
            s = max(0.0, min(s, dur - 1))
            e = max(s + 1, min(e, dur))
            jobs.append((s, e, None))
    if args.cut and not (args.auto or args.suggest):
        pass  # manual cuts only
    else:
        if has_audio(src):
            series = loudness_series(src)
            wins = find_peaks(series, dur, args.top)
            if not wins:
                print("No clear loud moments found — falling back to even splits.")
                wins = even_splits(dur, args.top)
        else:
            print("No audio track — falling back to even splits.")
            wins = even_splits(dur, args.top)
        jobs.extend((s, e, v) for s, e, v in wins)

    jobs.sort()
    if not jobs:
        sys.exit("Nothing to cut.")

    print(f"\n{len(jobs)} clip(s):")
    for i, (s, e, v) in enumerate(jobs, 1):
        tag = f"  (peak loudness {v:.1f})" if v else ""
        print(f"  {i}. {fmt(s)} - {fmt(e)}  ({e - s:.0f}s){tag}")

    if args.suggest:
        print("\nPreview only — nothing cut. Re-run with --auto or --cut to make them.")
        return

    os.makedirs(args.out, exist_ok=True)
    made = []
    for i, (s, e, _) in enumerate(jobs, 1):
        name = f"clip_{i:02d}_{fmt(s).replace(':', '')}-{fmt(e).replace(':', '')}.mp4"
        out_path = os.path.join(args.out, name)
        print(f"Cutting {i}/{len(jobs)} -> {out_path} ...")
        cut(src, s, e, out_path)
        made.append(out_path)

    print(f"\nDone — {len(made)} vertical clip(s) in {args.out}/")
    for m in made:
        print("  " + m)


if __name__ == "__main__":
    main()
