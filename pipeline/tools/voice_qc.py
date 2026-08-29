"""Check that an episode is narrated in ONE voice.

    python -m pipeline.tools.voice_qc episodes/ep01_knight_capital

Batched TTS buys quota at the cost of consistency: given a dozen lines in a single request
the model performs them as a set, and it will drop register for short punchy lines. EP01 v6
opened on "Nobody hacked them." at 115 Hz against a 154 Hz episode median — about five
semitones down — and the note back was "in the start there is some other voice".

Nothing in the render catches that: the clips are the right length, the words are right, the
schedule is right. It is only audible. So it gets measured instead.

Pitch is estimated by autocorrelation over voiced frames and reported per clip in semitones
from the episode median, because that is the unit ears actually work in. Anything past about
2.5 semitones starts to read as a different speaker.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np

from .. import config, script, tts

TOLERANCE = 2.5      # semitones from the median before a clip is called out
BAD_FRACTION = 0.10  # share of clips beyond tolerance that stops a build outright


def pitch(x: np.ndarray, sr: int, lo: float = 60.0, hi: float = 330.0) -> float:
    """Median F0 over voiced frames, or nan when there is not enough voiced audio."""
    win, hop = int(sr * 0.045), int(sr * 0.02)
    ests: list[float] = []
    for s in range(0, max(0, len(x) - win), hop):
        frame = x[s:s + win]
        if np.sqrt((frame ** 2).mean()) < 0.02:      # unvoiced or silence
            continue
        frame = frame - frame.mean()
        ac = np.correlate(frame, frame, "full")[win - 1:]
        a, b = int(sr / hi), int(sr / lo)
        if b >= len(ac):
            continue
        k = a + int(np.argmax(ac[a:b]))
        if ac[k] > 0.3 * ac[0]:                      # reject weak periodicity
            ests.append(sr / k)
    return float(np.median(ests)) if len(ests) > 8 else float("nan")


def measure(ep: Path, tolerance: float = TOLERANCE):
    """(clip count, median Hz, worst-first rows, flagged rows, 95th-pct spread).

    Split out from main() so the build can gate on it. A check that only exists as a
    command someone has to remember to type is a check that gets skipped on the episode
    that needed it — which is exactly what happened on EP02, where 51 of 130 clips came
    back beyond tolerance and nothing in the build said so.
    """
    doc = script.parse(ep / "script.md")
    lines = [tts.spoken_form(b.text) for b in doc.spoken]

    rows = []
    for i, text in enumerate(lines):
        path = ep / "out" / "vo" / f"line_{i:03d}.wav"
        if not path.exists():
            continue
        rows.append((i, text, pitch(tts.read_wav(path), config.SAMPLE_RATE)))
    if not rows:
        return 0, float("nan"), [], [], 0.0

    vals = np.array([r[2] for r in rows])
    good = vals[~np.isnan(vals)]
    med = float(np.median(good))
    cents = [(i, t, 12 * math.log2(p / med)) for i, t, p in rows if not np.isnan(p)]
    off = sorted(cents, key=lambda r: -abs(r[2]))
    flagged = [r for r in off if abs(r[2]) > tolerance]
    spread = float(np.percentile([abs(c) for _, _, c in cents], 95))
    return len(rows), med, off, flagged, spread


def gate(ep: Path, tolerance: float = TOLERANCE, *, halt: bool = True) -> int:
    """Post-synthesis voice check for build.py. Returns the flagged clip count.

    Halts before the render rather than after it. The audio is already cached by this
    point, so nothing paid for is lost — only the fifteen minutes of rendering an episode
    that would have to be re-rendered anyway once the voice is fixed.
    """
    n, med, off, flagged, spread = measure(ep, tolerance)
    if not off:
        return 0
    if not flagged:
        print(f"[voice] one voice throughout ({n} clips, median {med:.0f} Hz)")
        return 0
    i, _, c = off[0]
    print(f"[voice] {len(flagged)}/{n} clips beyond {tolerance:.1f} semitones "
          f"(95th pct {spread:.2f}, worst line {i} at {c:+.2f})")
    if halt and len(flagged) >= max(1, int(BAD_FRACTION * n)):
        raise SystemExit(
            f"[voice] STOP: {len(flagged)}/{n} clips are not the same voice. Inspect with\n"
            f"    python -m pipeline.tools.voice_qc {ep.name}\n"
            f"then re-synthesise the offending lines, or pass --ignore-voice to render anyway."
        )
    return len(flagged)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("episode", type=Path)
    ap.add_argument("--tolerance", type=float, default=TOLERANCE,
                    help="semitones from the median before a clip is flagged")
    ap.add_argument("--top", type=int, default=12, help="how many worst clips to list")
    args = ap.parse_args()

    ep = args.episode if args.episode.is_absolute() else config.ROOT / args.episode
    n, med, off, flagged, spread = measure(ep, args.tolerance)
    if not off:
        print(f"no clips in {ep / 'out' / 'vo'}", file=sys.stderr)
        return 1

    print(f"episode  : {ep.name}   voice {config.TTS_VOICE}")
    print(f"clips    : {n}   median pitch {med:.0f} Hz")
    print(f"spread   : 95th percentile {spread:.2f} semitones from median")
    print(f"flagged  : {len(flagged)} clip(s) beyond {args.tolerance:.1f} semitones\n")

    if flagged:
        print(f"{'idx':>4} {'semitones':>10}  line")
        for i, text, c in off[:args.top]:
            if abs(c) <= args.tolerance:
                break
            print(f"{i:>4} {c:>+10.2f}  {text[:62]}")
        print("\nRe-synthesise, or tighten the consistency clause in config.TTS_STYLE.")
        print("The first thirty seconds matter most — a register change there reads as a")
        print("second narrator before the viewer has settled into the first one.")
    else:
        print("One voice throughout.")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
