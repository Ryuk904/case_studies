"""Solve for the speaking rate that delivers a target WPM, from a real rendered episode.

Synthetic calibration passages lie. Two earlier attempts were off by 17% in opposite
directions: a single untrimmed line counts backend padding as speech, and a hand-picked
passage is never as digit-balanced as an actual script. The only number that does not lie
is a finished episode.

    python -m pipeline.tools.solve_rate episodes/ep01_knight_capital

The dial it solves for depends on the backend. edge has a real rate parameter; Gemini has
none, so pace is applied afterwards with ffmpeg's atempo and the dial is GEMINI_TEMPO.

On Gemini, run `python -m pipeline.tts --backfill <episode>` before changing the answer
into config. Tempo is part of the deliverable clip's fingerprint, so changing it makes every
clip stale — and a clip with no raw counterpart has to be bought from the API again.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .. import config, script, tts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("episode", type=Path)
    ap.add_argument("--targets", type=int, nargs="*", default=[140, 145, 150, 155])
    args = ap.parse_args()

    ep = args.episode if args.episode.is_absolute() else config.ROOT / args.episode
    doc = script.parse(ep / "script.md")
    wavs = sorted((ep / "out" / "vo").glob("line_*.wav"))
    if not wavs:
        print(f"no synthesised clips in {ep / 'out' / 'vo'} — run the build first",
              file=sys.stderr)
        return 1

    speech = sum(tts.duration_of(w) for w in wavs)
    words = sum(len(b.text.split()) for b in doc.spoken)

    # Fixed cost: inter-line gaps, explicit pauses, head/tail silence. Independent of rate,
    # which is exactly why solving by scaling the whole runtime gets the wrong answer.
    gaps = config.LINE_GAP * max(0, len(doc.spoken) - 1)
    pauses = sum(b.seconds for b in doc.beats if b.kind == "pause")
    fixed = gaps + pauses + config.HEAD_SILENCE + config.TAIL_SILENCE
    total = speech + fixed

    gemini = config.TTS_BACKEND == "gemini"
    dial = "GEMINI_TEMPO" if gemini else "TTS_RATE"
    cur_val = config.GEMINI_TEMPO if gemini else config.TTS_RATE

    print(f"episode : {ep.name}   backend {config.TTS_BACKEND}, voice {config.TTS_VOICE}")
    print(f"words   : {words} over {len(wavs)} clips")
    print(f"speech  : {speech:7.1f}s at {dial} = {cur_val}")
    print(f"fixed   : {fixed:7.1f}s  (gaps {gaps:.1f} + pauses {pauses:.1f} + head/tail "
          f"{config.HEAD_SILENCE + config.TAIL_SILENCE:.1f})")
    print(f"total   : {total:7.1f}s  = {int(total // 60)}m{int(total % 60):02d}s "
          f"-> {words / total * 60:.1f} WPM\n")

    cur_rate = float(re.sub(r"[%+]", "", config.TTS_RATE)) / 100.0

    print(f"{'target':>7} {'runtime':>9} {dial:>13} {'SPEECH_WPM':>11}")
    print("-" * 44)
    for target in args.targets:
        want = words / target * 60
        if want <= fixed:
            print(f"{target:>7} {'impossible':>9}")
            continue
        want_speech = want - fixed
        if gemini:
            answer = f"{config.GEMINI_TEMPO * speech / want_speech:.4f}"
        else:
            answer = f"{((1 + cur_rate) / (want_speech / speech) - 1) * 100:+.0f}%"
        print(f"{target:>7} {int(want // 60):>4}m{int(want % 60):02d}s {answer:>13} "
              f"{words / want_speech * 60:>11.1f}")

    print(f"\nPut the chosen row into config.{dial}, config.MEASURED_WPM (the target column)"
          f"\nand config.SPEECH_WPM (the last column), then re-run the build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
