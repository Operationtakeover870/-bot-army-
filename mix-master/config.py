# Mix & Master Bot — configuration.
# Every knob for the mastering chain lives here. Tweak values here,
# never inside the processing code.

# --- Loudness targets (streaming standard) ---
TARGET_LUFS = -14.0      # integrated loudness target (Spotify/YouTube normalize to -14)
TRUE_PEAK_DB = -1.0      # ceiling — nothing may peak above this (avoids clipping after MP3/AAC encoding)
LRA = 11.0               # loudness range target (keeps dynamics natural)

# --- EQ: corrective only, gentle ---
HIGHPASS_HZ = 28         # cut sub-bass rumble below this (inaudible mud)

# --- Glue compressor: evens out the mix, adds cohesion ---
COMP_THRESHOLD_DB = -18  # start compressing above this level
COMP_RATIO = 2.0         # 2:1 — gentle
COMP_ATTACK_MS = 20      # let transients (drum hits) through
COMP_RELEASE_MS = 200    # smooth release

# --- Stereo imaging: subtle widening ---
# extrastereo 'm' multiplies the L/R difference. 1.0 = untouched,
# 2.5 = filter default (strong). Keep small to stay mono-compatible.
STEREO_WIDTH = 1.4

# --- Safety limiter before loudness normalization ---
LIMITER_ATTACK_MS = 5
LIMITER_RELEASE_MS = 50

# --- Output ---
DEFAULT_FORMAT = "wav"   # wav or mp3
MP3_BITRATE = "320k"
