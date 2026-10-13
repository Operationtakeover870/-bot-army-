"""Write the mastering report: a short text file next to the mastered audio.

Two parts:
  - the numbers (measured in vs out)
  - plain-language summary of what the chain did
"""

import chain


def build_report(input_path, output_path, before, after, duration_s):
    lines = []
    lines.append("MIX & MASTER BOT — mastering report")
    lines.append("=" * 44)
    lines.append(f"Input:   {input_path}")
    lines.append(f"Output:  {output_path}")
    lines.append(f"Length:  {duration_s:.1f} seconds")
    lines.append("")
    lines.append("BEFORE (your mix):")
    lines.append(f"  Loudness:    {before['integrated_lufs']:.1f} LUFS")
    lines.append(f"  True peak:   {before['true_peak_db']:.1f} dB")
    lines.append(f"  Loudness range: {before['lra']:.1f} LU")
    lines.append("")
    lines.append("AFTER (mastered):")
    lines.append(f"  Loudness:    {after['integrated_lufs']:.1f} LUFS")
    lines.append(f"  True peak:   {after['true_peak_db']:.1f} dB")
    lines.append(f"  Loudness range: {after['lra']:.1f} LU")
    gain = after["integrated_lufs"] - before["integrated_lufs"]
    lines.append(f"  Gain applied: {'+' if gain >= 0 else ''}{gain:.1f} dB")
    lines.append("")
    lines.append("WHAT THE BOT DID:")
    for step in chain.describe_chain():
        lines.append(f"  {step}")
    lines.append("")
    lines.append(
        "In plain words: your mix was measured, cleaned up, gently squeezed "
        "so everything sits together, widened a touch, capped so it can't "
        "clip, and brought up (or down) to streaming loudness (-14 LUFS) — "
        "the level Spotify and YouTube expect. Nothing was guessed; the "
        "loudness gain was calculated from the actual measurement."
    )
    return "\n".join(lines) + "\n"


def write_report(path, text):
    with open(path, "w") as f:
        f.write(text)
