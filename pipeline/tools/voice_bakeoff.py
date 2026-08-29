"""Same passage, every candidate voice, at final settings. Listen and pick one.

    python -m pipeline.tools.voice_bakeoff

Writes out/voice_bakeoff/NN_<backend>_<voice>.wav plus a WPM table, so the choice is made
on how it sounds rather than on which model is newest.

Costs one API request per Gemini candidate, which on the free tier is a meaningful share of
a day's quota. Use --gemini-only or --edge-only to spend it deliberately.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import config, tts

# Deliberately a hook: numbers, a turn, and a line that needs a bit of menace.
PASSAGE = (
    "In 45 minutes, one of the biggest trading firms in America destroyed itself. "
    "Not because someone hacked it. "
    "Because of a switch nobody had removed in nine years."
)

EDGE_CANDIDATES = ["en-US-BrianMultilingualNeural", "en-US-AndrewMultilingualNeural"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--edge-only", action="store_true")
    ap.add_argument("--gemini-only", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    words = len(tts.spoken_form(PASSAGE).split())
    out = args.out or config.SCRATCH / "voice_bakeoff"
    out.mkdir(parents=True, exist_ok=True)

    plan: list[tuple[str, str]] = []
    if not args.gemini_only:
        plan += [("edge", v) for v in EDGE_CANDIDATES]
    if not args.edge_only:
        plan += [("gemini", v) for v in config.GEMINI_VOICE_CANDIDATES]

    original = config.TTS_BACKEND
    try:
        for i, (backend, voice) in enumerate(plan, 1):
            config.TTS_BACKEND = backend
            short = voice.split("-")[-1] if backend == "edge" else voice
            path = out / f"{i:02d}_{backend}_{short}.wav"
            try:
                clip = tts.synth(PASSAGE, path, voice=voice, cache=False)
                print(f"  {path.name:<34} {clip.duration:5.2f}s  "
                      f"{words / clip.duration * 60:5.1f} WPM", flush=True)
            except Exception as exc:                               # noqa: BLE001
                print(f"  {path.name:<34} FAILED {str(exc)[:70]}", flush=True)
    finally:
        config.TTS_BACKEND = original

    print(f"\n{words} words · tempo {config.GEMINI_TEMPO} · model {config.GEMINI_TTS_MODEL}")
    print(f"-> {out}")
    print("Set the winner in config.VOICE_BY_BACKEND, then re-solve the rate:")
    print("  python -m pipeline.tools.solve_rate <episode>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
