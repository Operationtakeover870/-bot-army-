"""Loudness analysis: measure a file's LUFS / true peak / LRA using FFmpeg.

Uses FFmpeg's loudnorm filter in analysis mode (first pass of the
two-pass loudness workflow). Returns the measured values the mastering
chain needs, plus a plain summary for the report.
"""

import json
import re
import subprocess


class AnalysisError(Exception):
    pass


def probe_duration(path):
    """Return duration in seconds via ffprobe (0.0 if unknown)."""
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30,
        )
        return float(p.stdout.strip())
    except Exception:
        return 0.0


def measure_loudness(path):
    """Measure integrated loudness, true peak and LRA. Raises AnalysisError."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", path,
        "-af", "loudnorm=print_format=json",
        "-f", "null", "-",
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        raise AnalysisError("ffmpeg not found on this machine.")
    except subprocess.TimeoutExpired:
        raise AnalysisError("loudness analysis timed out.")

    match = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.DOTALL)
    if not match:
        raise AnalysisError(
            "could not measure loudness — file may be too short, silent, or unreadable."
        )
    data = json.loads(match.group(0))
    return {
        "integrated_lufs": float(data["input_i"]),
        "true_peak_db": float(data["input_tp"]),
        "lra": float(data["input_lra"]),
        "threshold_db": float(data["input_thresh"]),
        "offset_db": float(data["target_offset"]),
        "raw": data,
    }
