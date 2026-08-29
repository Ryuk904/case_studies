"""Sample frames out of a rendered episode and tile them into one image.

This is the check that has caught every layout regression in this pipeline. A scene can
lay out correctly in isolation and still be wrong in the finished video, because timing
decides which moment of a draw-on animation you actually see, and a half-drawn diagram is
where overlaps show up.

    python -m pipeline.tools.frames episodes/ep01_knight_capital
    python -m pipeline.tools.frames episodes/ep01_knight_capital --at 12 47 210

Default is 12 evenly spaced frames. Pass --at with seconds to look at specific moments.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from .. import config


def _ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _duration(video: Path) -> float:
    """Seconds, read back from the container rather than assumed from the schedule."""
    out = subprocess.run(
        [_ffmpeg(), "-i", str(video)], capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "Duration:" in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"could not read duration of {video}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("episode", type=Path)
    ap.add_argument("--at", type=float, nargs="*", help="timestamps in seconds")
    ap.add_argument("--n", type=int, default=12, help="how many evenly spaced frames")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    ep = args.episode if args.episode.is_absolute() else config.ROOT / args.episode
    video = ep if ep.suffix == ".mp4" else ep / "out" / "episode.mp4"
    if not video.exists():
        print(f"no rendered video at {video}", file=sys.stderr)
        return 1

    if args.at:
        times = list(args.at)
    else:
        dur = _duration(video)
        # Inset from both ends: the first and last frames are the head/tail silence, which
        # tells you nothing about whether the episode looks right.
        times = [dur * (i + 0.5) / args.n for i in range(args.n)]

    from PIL import Image, ImageDraw

    tw, th = 640, 360
    rows = (len(times) + args.cols - 1) // args.cols
    sheet = Image.new("RGB", (tw * args.cols, th * rows), (26, 26, 30))
    draw = ImageDraw.Draw(sheet)

    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            shot = Path(tmp) / f"f{i:03d}.png"
            subprocess.run(
                [_ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{t:.3f}",
                 "-i", str(video), "-frames:v", "1", str(shot)], check=True)
            with Image.open(shot) as im:
                im = im.convert("RGB").resize((tw - 8, th - 8), Image.LANCZOS)
                col, row = i % args.cols, i // args.cols
                sheet.paste(im, (col * tw + 4, row * th + 4))
                draw.text((col * tw + 14, row * th + 14),
                          f"{int(t // 60)}:{t % 60:04.1f}", fill=(255, 60, 80))

    out = args.out or ep / "out" / "frames.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"wrote {out}  ({len(times)} frames from {video.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
