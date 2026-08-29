"""Frame schedule -> episode.mp4.

Owns encoding only. It never decides what appears or when: that is scenes.py and
schedule.py. Keeping that boundary means a timing bug is never also a drawing bug.
"""

from __future__ import annotations

import contextlib
import subprocess
import sys
import time
from pathlib import Path

from . import config, scenes, sketch
from .schedule import Schedule


def _writer(path: Path, audio_path: Path | None, fps: int):
    import imageio_ffmpeg
    return imageio_ffmpeg.write_frames(
        str(path), (config.W, config.H), fps=fps,
        codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
        quality=None, bitrate=None,
        macro_block_size=1,          # 1920x1080 is already divisible; no silent rescale
        ffmpeg_log_level="error",
        # CRF 16, not 18. This content is flat vector-like fills, so CRF 18 encodes an
        # 8-minute episode at ~74 kb/s of video. That is "correct" for the source, but
        # YouTube re-encodes what it receives, and thin sketch strokes and small type are
        # exactly what a second lossy pass smears. Spending ~9MB more on the master keeps
        # the edges crisp downstream.
        output_params=["-preset", "slow", "-crf", "16", "-movflags", "+faststart"],
        audio_path=str(audio_path) if audio_path else None,
        audio_codec="aac" if audio_path else None,
    )


def _ease_io(t: float) -> float:
    """Ease in and out. A linear wipe reads as a mechanical swipe; this reads as a cut."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def verify(mp4: Path, expected_frames: int) -> bool:
    """Decode the finished file and count frames.

    Non-optional. The tiny_rules pipeline lost hours to renders that reported every frame
    sent while the encoder silently dropped half of them, producing a file that looked
    fine in a thumbnail and was missing its first half on playback.
    """
    import imageio_ffmpeg
    proc = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(mp4), "-map", "0:v",
         "-f", "null", "-", "-v", "info"],
        capture_output=True, text=True,
    )
    got = 0
    for token in reversed(proc.stderr.split()):
        if token.startswith("frame="):
            got = int(token.split("=")[1] or 0)
            break
    if got == 0:
        for line in reversed(proc.stderr.splitlines()):
            if "frame=" in line:
                got = int(line.split("frame=")[1].split()[0])
                break

    ok = abs(got - expected_frames) <= 1
    status = "OK" if ok else "MISMATCH"
    print(f"[verify] {status}: encoder sent {expected_frames}, file decodes {got}")
    if not ok:
        print("[verify] Do NOT upload this file. See PIPELINE.md, render gotcha.")
    return ok


def run(sched: Schedule, out_dir: Path, *, smoke: bool = False,
        name: str = "episode", keep_audio: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4 = out_dir / (f"{name}_smoke.mp4" if smoke else f"{name}.mp4")
    wav = out_dir / "master.wav"
    sched.write_audio(wav)
    if sched.chapters:
        # Only the canonical render owns chapters.txt. A --dry proof has estimated timings
        # for any unvoiced line, and letting it overwrite the file that seo.md's chapter
        # list and `lint --timing` both read would put guessed timecodes into a published
        # description with nothing marking them as guesses.
        stem = "chapters" if name == "episode" else f"{name}_chapters"
        sched.write_chapters(out_dir / f"{stem}.txt")

    n = sched.n_frames
    print(f"[render] {sched.duration:.2f}s · {n} frames · {config.W}x{config.H}@{config.FPS}"
          + (" · SMOKE" if smoke else ""))

    writer = _writer(mp4, wav, config.FPS)
    writer.send(None)

    started = time.time()
    logged: set[int] = set()
    last_surf = None            # last frame drawn, held so a cut can wipe out of it
    last_key: int | None = None
    trans_from, trans_start = None, 0.0
    for i in range(n):
        t = i / config.FPS
        visual, local_t, seg_dur = sched.at(t)

        # One line per scene entry, with its real timestamp — this is what the chapter
        # list in seo.md is built from. Never hand-estimate a chapter.
        key = id(visual)
        if key not in logged:
            logged.add(key)
            label = visual.renderer if visual else "blank"
            print(f"[scene] {label} @ {t:.2f}s")

        surf, ctx = sketch.new_surface()
        scenes.render(ctx, visual, local_t, seg_dur)

        # Transition. For the first fraction of a second after a scene change, wipe the new
        # frame in over the last frame of the old one, led by an accent bar. Hard cuts
        # between static frames are what made the first cut feel like a slide deck; this is
        # the cheapest possible thing that makes it feel cut rather than paged.
        #
        # A scene can override it with cut="hard" (a near-instant snap, for a beat that
        # should land like a slap) or cut="soft" (a slow dissolve, for a change of subject).
        # One wipe for a whole episode is its own kind of monotony.
        style = (visual.get("cut") if visual else "") or "wipe"
        secs = {"hard": 0.07, "soft": 0.62}.get(style, config.TRANSITION)
        if key != last_key:
            trans_from, trans_start, last_key = last_surf, t, key
        if trans_from is not None and t - trans_start < secs:
            p = _ease_io((t - trans_start) / secs)
            out, octx = sketch.new_surface()
            octx.set_source_surface(trans_from, 0, 0)
            octx.paint()
            if style == "soft":
                # Cross-dissolve: no moving edge at all, so it reads as a change of chapter
                # rather than a change of slide.
                octx.set_source_surface(surf, 0, 0)
                octx.paint_with_alpha(p)
            else:
                edge = round(config.W * p)
                octx.save()
                octx.rectangle(0, 0, edge, config.H)
                octx.clip()
                octx.set_source_surface(surf, 0, 0)
                octx.paint()
                octx.restore()
                if 0.0 < p < 1.0:
                    octx.set_source_rgb(*config.ACCENT)
                    octx.rectangle(edge - 7, 0, 7, config.H)
                    octx.fill()
            surf = out
        elif trans_from is not None:
            trans_from = None

        last_surf = surf
        writer.send(sketch.surface_to_rgb(surf).tobytes())

        if i % 60 == 0 and i:
            rate = i / (time.time() - started)
            eta = (n - i) / max(rate, 1e-6)
            sys.stdout.write(f"\r[render] {i}/{n}  {rate:.1f} fps  eta {eta:5.0f}s")
            sys.stdout.flush()

    writer.close()
    elapsed = time.time() - started
    print(f"\n[render] done in {elapsed:.0f}s -> {mp4}")

    # Hard-fail the build. Computing the check and discarding the result means a
    # frame-dropped render exits 0 and gets reported as finished, which is precisely the
    # silent corruption the verify step exists to catch.
    if not verify(mp4, n):
        raise SystemExit(f"[render] ABORT: frame count mismatch in {mp4}")

    # The master is an intermediate: it is already inside the mp4, it is ~50MB an episode,
    # and it rebuilds from the clip cache in seconds with no API cost. Dropped only after
    # the frame check passes, so a failed render still has its audio for diagnosis.
    if not keep_audio:
        with contextlib.suppress(OSError):
            wav.unlink()
    return mp4
