"""Episode entry point.

Thin by design. All real logic lives in pipeline/ so that fixing a rendering bug fixes it
for every episode, past and future. If this file grows past ~40 lines, whatever it is doing
belongs in pipeline/.

    python build.py --smoke    ~20s visual dry run of every scene, spends no API quota
    python build.py --dry      full length, real pace, silence for any line not yet voiced
    python build.py            full 1080p render

Launch long renders through the Bash tool with a shell redirect, never PowerShell
Start-Process -RedirectStandardOutput. See PIPELINE.md.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline import render, schedule, script, tts   # noqa: E402
from pipeline.tools import clip_qc, voice_qc         # noqa: E402

EP = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="fast dry run of every scene")
    ap.add_argument("--dry", action="store_true",
                    help="full length from cached audio only; never calls the backend")
    ap.add_argument("--ignore-voice", action="store_true",
                    help="render even if the narration is not in one voice")
    ap.add_argument("--ignore-clips", action="store_true",
                    help="render even if a clip is far longer than its line")
    args = ap.parse_args()

    doc = script.parse(EP / "script.md")
    print(f"[build] {len(doc.spoken)} spoken lines, {doc.words_by_section()}")
    lines = [b.text for b in doc.spoken]

    if args.smoke:
        clips = tts.dummy_clips(lines)
    elif args.dry:
        clips, guessed = tts.dry_clips(lines, EP / "out" / "vo")
        print(f"[build] DRY: {len(clips) - guessed} voiced, {guessed} estimated. "
              f"Proof only — estimated timings are guesses, never ship this file.")
    else:
        clips = tts.synth_lines(lines, EP / "out" / "vo")
        # Length first: a hallucinated clip poisons the pitch median voice_qc measures
        # against, so a voice-first order flags innocent clips and misses the broken one.
        clip_qc.gate(EP, halt=not args.ignore_clips)
        voice_qc.gate(EP, halt=not args.ignore_voice)

    sched = schedule.build(doc, clips, smoke=args.smoke)
    render.run(sched, out_dir=EP / "out", smoke=args.smoke,
               name="episode_dry" if args.dry else "episode")


if __name__ == "__main__":
    main()
