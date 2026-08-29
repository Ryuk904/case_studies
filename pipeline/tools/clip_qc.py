"""Check that every clip is the LENGTH its line implies.

    python -m pipeline.tools.clip_qc episodes/ep05_roblox_consul

Written on EP05, 2026-08-12, after the first eight clips of the first Gemini/Iapetus run
came back like this:

    line 6   16 words   31.04 s     30.9 WPM
    line 7    7 words   37.16 s     11.3 WPM

Neither is a slow read. Measured on the envelope, both clips are **78% voiced** across
their whole length: the model is talking continuously for thirty-odd seconds. The prompt
sent to Gemini is `f"{TTS_STYLE}\n\n{text}"` (tts.py), and `TTS_STYLE` is now four
sentences of delivery direction — so when a line is short relative to the instruction, the
model sometimes performs the *instruction* as well as the line.

It is intermittent, not deterministic: line 1 is also seven words and came back correct at
3.88 s. So a fraction of any episode's clips can be garbage, and:

**`voice_qc` cannot see this.** It measures pitch deviation from the episode median. A
hallucinated thirty-second clip in the right voice passes it cleanly. Every other check in
the build is downstream of the measured durations, so it does not see a problem either —
`schedule.py` simply believes the clip and stretches the frame to match, and the render
comes out minutes too long with narration nobody wrote. Nothing in the pipeline was
looking at whether a clip's length is *plausible*.

The check is deliberately crude and one-sided. Speaking rate varies a lot line to line
(digits are slow, short lines carry proportionally more trim padding), so a tight band
would cry wolf. A clip running several times its expected length is never prosody.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import config, script, tts

# A clip may run this many times its word-count estimate before it is called a defect,
# plus a flat allowance so that short lines are not judged on a two-word denominator.
MAX_RATIO = 2.4
FLAT_ALLOWANCE = 2.5     # seconds


def measure(ep: Path) -> list[tuple[int, str, float, float]]:
    """(index, text, measured seconds, expected seconds) for every clip on disk."""
    doc = script.parse(ep / "script.md")
    sps = config.SPEECH_WPM / 60.0
    rows = []
    for i, beat in enumerate(doc.spoken):
        path = ep / "out" / "vo" / f"line_{i:03d}.wav"
        if not path.exists():
            continue
        secs = len(tts.read_wav(path)) / config.SAMPLE_RATE
        rows.append((i, beat.text, secs, len(beat.text.split()) / sps))
    return rows


def flagged(rows) -> list[tuple[int, str, float, float]]:
    return [r for r in rows if r[2] > r[3] * MAX_RATIO + FLAT_ALLOWANCE]


def gate(ep: Path, *, halt: bool = True) -> int:
    """Post-synthesis length check for build.py. Returns the flagged clip count.

    Runs BEFORE voice_qc: a hallucinated clip poisons the pitch median that voice_qc
    measures everything else against, so checking voice first can flag a dozen innocent
    clips and stay silent about the one that is actually broken.
    """
    rows = measure(ep)
    bad = flagged(rows)
    if not rows:
        return 0
    if not bad:
        print(f"[clip] {len(rows)} clips, all within {MAX_RATIO:.1f}x of expected length")
        return 0
    print(f"[clip] {len(bad)}/{len(rows)} clips are far longer than their line:")
    for i, text, secs, exp in bad[:10]:
        print(f"[clip]   line {i:>3}  {secs:6.2f}s vs {exp:5.2f}s expected  "
              f"({secs / max(exp, 1e-6):.1f}x)  {text[:52]}")
    if halt:
        raise SystemExit(
            f"[clip] STOP: {len(bad)} clip(s) contain speech that is not in the script.\n"
            f"    The model performs TTS_STYLE as well as the line when the line is short\n"
            f"    relative to the instruction. Delete those clips and their .fingerprint\n"
            f"    sidecars from out/vo/ and out/vo/raw/ to re-roll them, or shorten\n"
            f"    config.TTS_STYLE, which re-buys the whole episode.\n"
            f"    Pass --ignore-clips to render anyway."
        )
    return len(bad)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("episode", type=Path)
    ap.add_argument("--all", action="store_true", help="list every clip, not just defects")
    args = ap.parse_args()

    ep = args.episode if args.episode.is_absolute() else config.ROOT / args.episode
    rows = measure(ep)
    if not rows:
        print(f"no clips in {ep / 'out' / 'vo'}", file=sys.stderr)
        return 1

    bad = {r[0] for r in flagged(rows)}
    words = sum(len(t.split()) for i, t, _, _ in rows if i not in bad)
    secs = sum(s for i, _, s, _ in rows if i not in bad)
    print(f"episode : {ep.name}   voice {config.TTS_VOICE}")
    print(f"clips   : {len(rows)}   flagged {len(bad)}")
    if secs:
        print(f"rate    : {words / secs * 60:.1f} WPM over the clips that are not flagged "
              f"(config.SPEECH_WPM = {config.SPEECH_WPM})")
    print()
    print(f"{'idx':>4} {'secs':>7} {'expect':>7} {'ratio':>6}  line")
    for i, text, s, e in rows:
        if not args.all and i not in bad:
            continue
        mark = "  <-- DEFECT" if i in bad else ""
        print(f"{i:>4} {s:>7.2f} {e:>7.2f} {s / max(e, 1e-6):>6.1f}  {text[:50]}{mark}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
