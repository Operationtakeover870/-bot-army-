"""Build the FFmpeg mastering filter chain.

Chain order (standard mastering order):
  1. highpass        — cut inaudible sub-rumble
  2. acompressor     — gentle glue compression
  3. extrastereo     — subtle stereo widening
  4. alimiter        — safety ceiling so nothing clips
  5. loudnorm        — two-pass loudness normalization to streaming target

The loudnorm stage uses the measured values from analyze.measure_loudness
(second pass of the two-pass workflow), so the gain is exact, not guessed.
"""

import config


def _db_to_linear(db):
    return 10 ** (db / 20.0)


def build_chain(measured):
    """Return the FFmpeg -af filter string for the full mastering chain."""
    cfg = config
    limiter_ceiling = _db_to_linear(cfg.TRUE_PEAK_DB)

    loudnorm = (
        "loudnorm="
        f"I={cfg.TARGET_LUFS}:"
        f"TP={cfg.TRUE_PEAK_DB}:"
        f"LRA={cfg.LRA}:"
        f"measured_I={measured['integrated_lufs']:.2f}:"
        f"measured_TP={measured['true_peak_db']:.2f}:"
        f"measured_LRA={measured['lra']:.2f}:"
        f"measured_thresh={measured['threshold_db']:.2f}:"
        f"offset={measured['offset_db']:.2f}:"
        "linear=true"
    )

    stages = [
        f"highpass=f={cfg.HIGHPASS_HZ}",
        (
            "acompressor="
            f"threshold={cfg.COMP_THRESHOLD_DB}dB:"
            f"ratio={cfg.COMP_RATIO}:"
            f"attack={cfg.COMP_ATTACK_MS}:"
            f"release={cfg.COMP_RELEASE_MS}"
        ),
        f"extrastereo=m={cfg.STEREO_WIDTH}",
        (
            "alimiter="
            f"limit={limiter_ceiling:.6f}:"
            f"attack={cfg.LIMITER_ATTACK_MS}:"
            f"release={cfg.LIMITER_RELEASE_MS}"
        ),
        loudnorm,
    ]
    return ",".join(stages)


def describe_chain():
    """Plain-language description of each stage, for the report."""
    cfg = config
    return [
        f"1. Sub-bass cleanup — cut everything below {cfg.HIGHPASS_HZ} Hz (rumble you can't hear, eats headroom).",
        f"2. Glue compression — gentle {cfg.COMP_RATIO}:1 compression above {cfg.COMP_THRESHOLD_DB} dB, "
        f"{cfg.COMP_ATTACK_MS} ms attack / {cfg.COMP_RELEASE_MS} ms release (evens out the mix, keeps punch).",
        f"3. Stereo width — subtle widening (x{cfg.STEREO_WIDTH}), stays mono-compatible.",
        f"4. Safety limiter — ceiling at {cfg.TRUE_PEAK_DB} dB so nothing clips.",
        f"5. Loudness match — two-pass normalization to {cfg.TARGET_LUFS} LUFS "
        f"(the Spotify/YouTube standard), true peak {cfg.TRUE_PEAK_DB} dB, LRA {cfg.LRA}.",
    ]
