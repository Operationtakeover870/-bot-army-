# Show Bot (Bot #5)

Prompt in, animated episode out. Antonio's own show studio — no subscription, no credits meter.

## How it works

1. **Premise** — Antonio gives ICE a concept ("a funny episode about two roommates fighting over pizza").
2. **Script** — ICE writes the episode: scenes with dialogue, narrator lines, comedic timing.
3. **Scenes** — AI-generated cartoon visuals, one per scene (16:9).
4. **Voices** — each character gets a distinct voice via TTS; narrator sets the tone.
5. **Assemble** — `assemble.py` brings it together: Ken Burns motion on every scene
   (slow zoom / pan, cycled so it never feels static), dialogue timed to visuals,
   scenes concatenated into one 1280x720 MP4.

## Files

- `assemble.py` — the assembly engine. Takes a manifest JSON:
  ```json
  {
    "title": "Episode Title",
    "output": "episode.mp4",
    "scenes": [
      {"image": "scene1.png", "audio": "scene1.mp3"},
      {"image": "scene2.png", "audio": "scene2.mp3"}
    ]
  }
  ```
  Run: `python3 assemble.py manifest.json`
- `ep1/` — proof-of-concept episode: "The Last Slice" (46s, 3 scenes).

## Workflow

Nothing for Antonio to install. He sends a premise in chat → ICE writes, voices,
draws, and assembles → the episode comes back in chat, ready to post.

## Notes

- Pure stdlib + ffmpeg + TTS + image generation. Zero marginal cost per episode.
- Style is animated-cartoon, not photoreal — same lane as Showrunner, owned outright.
- Episode length scales with the script: more scenes = longer episode.
