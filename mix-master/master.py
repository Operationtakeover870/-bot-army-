#!/usr/bin/env python3
"""Mix & Master Bot v1 — feed it a stereo mix, get back a mastered file.

Usage:
    python3 master.py input.wav
    python3 master.py input.mp3 -o mastered_song.wav
    python3 master.py input.wav --target -14 --format mp3

What it does:
    1. Measures your mix (loudness, true peak, dynamics).
    2. Runs it through the mastering chain (see chain.py).
    3. Writes the mastered file + a text report of what it did.
"""

import argparse
import os
import subprocess
import sys

import analyze
import chain
import config
import report as report_mod


def run_master(input_path, output_path, target_lufs):
    if not os.path.isfile(input_path):
        print(f"error: input file not found: {input_path}")
        return 1

    # Allow a custom loudness target for this run.
    config.TARGET_LUFS = target_lufs

    print("measuring your mix...")
    try:
        before = analyze.measure_loudness(input_path)
    except analyze.AnalysisError as e:
        print(f"error: {e}")
        return 1
    duration = analyze.probe_duration(input_path)
    print(f"  in:  {before['integrated_lufs']:.1f} LUFS, "
          f"peak {before['true_peak_db']:.1f} dB")

    print("mastering...")
    filters = chain.build_chain(before)
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-y",
        "-i", input_path,
        "-af", filters,
        "-ar", "44100", "-ac", "2",
    ]
    if output_path.lower().endswith(".mp3"):
        cmd += ["-codec:a", "libmp3lame", "-b:a", config.MP3_BITRATE]
    else:
        cmd += ["-codec:a", "pcm_s16le"]
    cmd.append(output_path)

    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 or not os.path.isfile(output_path):
        print("error: mastering failed.")
        print(p.stderr[-1500:])
        return 1

    print("verifying the master...")
    after = analyze.measure_loudness(output_path)

    report_text = report_mod.build_report(input_path, output_path, before, after, duration)
    report_path = output_path + ".report.txt"
    report_mod.write_report(report_path, report_text)

    print(f"  out: {after['integrated_lufs']:.1f} LUFS, "
          f"peak {after['true_peak_db']:.1f} dB")
    print(f"done.\n  master: {output_path}\n  report: {report_path}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Mix & Master Bot v1")
    ap.add_argument("input", help="stereo mix file (wav or mp3)")
    ap.add_argument("-o", "--output", default=None,
                    help="output file (default: <input>_mastered.wav)")
    ap.add_argument("--target", type=float, default=config.TARGET_LUFS,
                    help="target loudness in LUFS (default -14)")
    ap.add_argument("--format", choices=["wav", "mp3"], default=config.DEFAULT_FORMAT,
                    help="output format (default wav)")
    args = ap.parse_args()

    if args.output:
        output_path = args.output
    else:
        base, _ = os.path.splitext(args.input)
        output_path = f"{base}_mastered.{args.format}"

    return run_master(args.input, output_path, args.target)


if __name__ == "__main__":
    sys.exit(main())
