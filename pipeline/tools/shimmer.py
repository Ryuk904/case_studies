"""Diff consecutive frames of a rendered episode to find sub-pixel motion.

The pixel-grid rule in PIPELINE.md exists because it was broken once and shipped: moving
the frame origin by a fraction of a pixel re-antialiases every glyph edge thirty times a
second, which reads on screen as the type vibrating and spends h264 bitrate on noise
instead of edges. It is invisible in a still and obvious in motion, which is the worst
possible combination, so it has to be measured.

    python -m pipeline.tools.shimmer episodes/ep02_cloudflare_regex --at 20 95 300

Pick timestamps inside scenes that should be STILL — a title card mid-hold, a metric card
after its count has landed. A scene with something deliberately moving in it (the gauge
needle, the backtrack counter, the dashboard bars) will report a large diff and that is
the feature working.

Reference numbers, measured on a static title card during the EP01 investigation:

    sub-pixel drift   15,947 changed px/frame   max delta 141
    integer drift          0                              0

The threshold below is deliberately loose. h264 at CRF 16 is not lossless, so a handful of
pixels will differ by 1 or 2 in flat areas; what a shimmer bug looks like is thousands of
pixels differing by 20 or more, all of them on a glyph or stroke edge.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from .. import config

DELTA = 20        # per-channel difference that counts as a real change, not encoder noise
BUDGET = 400      # changed pixels above DELTA that a still scene is allowed


def _ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def sample(video: Path, at: float, n: int, tmp: Path) -> list[Path]:
    """Decode `n` consecutive frames starting at `at` seconds."""
    out = tmp / f"t{at:.0f}"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [_ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{at:.3f}", "-i", str(video),
         "-frames:v", str(n), str(out / "f%03d.png")], check=True)
    return sorted(out.glob("f*.png"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("episode", type=Path)
    ap.add_argument("--at", type=float, nargs="+", required=True,
                    help="timestamps (seconds) inside scenes that should be still")
    ap.add_argument("--frames", type=int, default=10)
    ap.add_argument("--delta", type=int, default=DELTA)
    ap.add_argument("--budget", type=int, default=BUDGET)
    args = ap.parse_args()

    import numpy as np
    from PIL import Image

    ep = args.episode if args.episode.is_absolute() else config.ROOT / args.episode
    video = ep if ep.suffix == ".mp4" else ep / "out" / "episode.mp4"
    if not video.exists():
        print(f"no rendered video at {video}", file=sys.stderr)
        return 1

    worst = 0
    print(f"{'at':>8}  {'pairs':>5}  {'max changed px':>14}  {'max delta':>9}   verdict")
    print("-" * 62)
    with tempfile.TemporaryDirectory() as tmpdir:
        for at in args.at:
            shots = sample(video, at, args.frames, Path(tmpdir))
            if len(shots) < 2:
                print(f"{at:>8.1f}  could not decode two frames")
                continue
            arrs = [np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)
                    for p in shots]
            changed_max, delta_max = 0, 0
            for a, b in zip(arrs, arrs[1:]):
                diff = np.abs(a - b).max(axis=2)
                changed = int((diff > args.delta).sum())
                changed_max = max(changed_max, changed)
                delta_max = max(delta_max, int(diff.max()))
            worst = max(worst, changed_max)
            verdict = "still" if changed_max <= args.budget else "MOVING"
            print(f"{at:>8.1f}  {len(arrs) - 1:>5}  {changed_max:>14,}  "
                  f"{delta_max:>9}   {verdict}")

    print(f"\nworst: {worst:,} changed px/frame above delta {args.delta} "
          f"(budget {args.budget:,})")
    print("A scene with intentional motion SHOULD report MOVING. Only a scene that is "
          "meant to be held still and is not is a bug.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
