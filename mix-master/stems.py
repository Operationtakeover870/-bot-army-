"""Stem-level mixing — NOT built yet. This module is the open door.

The v1 bot masters a finished stereo mix (one file in, one file out).
When stem mixing is added, this module will hold:

  - StemMixer: takes individual stems (vocals.wav, drums.wav, bass.wav, ...)
  - per-stem leveling, EQ and panning
  - stem bus summing into a stereo mix
  - which then feeds the mastering chain in chain.py

Nothing here runs yet on purpose — one bot, one objective at a time.
Mastering first, stem mixing next.
"""


class StemMixer:
    """Placeholder for future stem-level mixing. Do not use yet."""

    def __init__(self, stems):
        self.stems = stems

    def mix(self):
        raise NotImplementedError(
            "Stem mixing is not implemented yet. "
            "Export your stems as one stereo mix and master that with master.py."
        )
