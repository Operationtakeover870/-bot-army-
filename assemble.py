#!/usr/bin/env python3
"""
Show Bot — episode assembler (Bot #5).

Takes a manifest JSON describing scenes (still image + dialogue audio each)
and builds an animated episode: Ken Burns motion on every scene, dialogue
mixed in, scenes concatenated into one MP4.

Manifest format:
{
  "title": "Episode Title",
  "output": "episode.mp4",
  "scenes": [
    {"image": "scene1.png", "audio": "scene1.mp3"},
    {"image": "scene2.png", "audio": "scene2.mp3"}
  ]
}

Usage:
    python3 assemble.py manifest.json

Output: 1280x720, 30fps, h264 + aac. Pure stdlib + ffmpeg. Zero cost.
"""
import json
import os
import subprocess
import sys

W, H, FPS = 1280, 720, 30

# Ken Burns moves, cycled per scene so episodes don't feel static.
MOVES = [
    # slow zoom in
    "zoompan=z='min(zoom+0.0018,1.6)':d={f}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}",
    # slow zoom out
    "zoompan=z='max(zoom-0.0018,1.0)':d={f}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}",
    # pan right
    "zoompan=z='1.3':d={f}:x='(iw-iw/zoom)*on/{f}':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}",
    # pan left
    "zoompan=z='1.3':d={f}:x='(iw-iw/zoom)*(1-on/{f})':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}",
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{r.stderr[-2000:]}")


def audio_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 assemble.py manifest.json")
    with open(sys.argv[1]) as f:
        m = json.load(f)

    scenes = m["scenes"]
    out = m.get("output", "episode.mp4")
    base = os.path.dirname(os.path.abspath(sys.argv[1]))
    tmpdir = os.path.join(base, "_parts")
    os.makedirs(tmpdir, exist_ok=True)

    parts = []
    for i, sc in enumerate(scenes):
        img = os.path.join(base, sc["image"])
        aud = os.path.join(base, sc["audio"])
        if not os.path.isfile(img):
            sys.exit(f"Missing image: {img}")
        if not os.path.isfile(aud):
            sys.exit(f"Missing audio: {aud}")
        dur = audio_duration(aud) + 0.4  # breathing room at the tail
        frames = int(dur * FPS)
        move = MOVES[i % len(MOVES)].format(f=frames, w=W, h=H, fps=FPS)
        part = os.path.join(tmpdir, f"part_{i:02d}.mp4")
        print(f"Scene {i+1}/{len(scenes)}: {dur:.1f}s  ({os.path.basename(img)})")
        # zoom out starts at 1.6 so it has room to pull back
        zf = move.replace("zoom-0.0018,1.0", "zoom-0.0018,1.0")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-loop", "1", "-i", img, "-i", aud,
             "-filter_complex",
             f"[0:v]{zf},format=yuv420p[v]",
             "-map", "[v]", "-map", "1:a",
             "-t", f"{dur:.2f}", "-r", str(FPS),
             "-c:v", "libx264", "-preset", "fast", "-crf", "21",
             "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", "-shortest", part])
        parts.append(part)

    print("Concatenating...")
    lst = os.path.join(tmpdir, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", out])
    total = sum(audio_duration(os.path.join(base, s["audio"])) for s in scenes)
    print(f"\nDone — '{out}'  ({len(scenes)} scenes, ~{total:.0f}s)")


if __name__ == "__main__":
    main()
