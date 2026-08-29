"""Beats + measured clip durations -> a frame schedule and a master audio track.

This is the module that makes the pipeline work without a human editor. Video timing is
*derived* from real, measured audio durations, so picture and sound cannot drift. Nothing
here estimates how long anything takes.

Named schedule.py rather than timeline.py because `timeline` is already a scene renderer,
and two different things called timeline in one codebase is a bug waiting to happen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import config, sfx, tts
from .script import Beat, Script, Visual

SMOKE_SEGMENT = 0.6      # seconds per visual in a --smoke dry run


@dataclass
class Segment:
    """One visual's span on screen."""
    start: float
    end: float
    visual: Visual | None

    @property
    def duration(self) -> float:
        return max(1e-6, self.end - self.start)


@dataclass
class Schedule:
    segments: list[Segment]
    audio: np.ndarray
    duration: float
    chapters: list[tuple[float, str]] = field(default_factory=list)
    # Beat ranges whose visuals opted into the darker ambient bed (mood="dark").
    dark_ranges: list[tuple[float, float]] = field(default_factory=list)

    @property
    def n_frames(self) -> int:
        return max(1, int(round(self.duration * config.FPS)))

    def at(self, t: float) -> tuple[Visual | None, float, float]:
        """Visual on screen at t, progress 0..1 through its span, and its length in seconds.

        The duration is part of the contract because scene animations are timed in real
        seconds, not as a fraction of however long the beat happens to be.
        """
        for seg in self.segments:
            if seg.start <= t < seg.end:
                return seg.visual, (t - seg.start) / seg.duration, seg.duration
        last = self.segments[-1] if self.segments else None
        return (last.visual if last else None), 1.0, (last.duration if last else 1.0)

    def write_audio(self, path: Path) -> None:
        mix = self.audio
        if config.MUSIC_GAIN > 0:
            # Bed under the voice, keyed to this episode's own chapter marks so the drone
            # changes where the story does. Mixed here rather than baked into self.audio so
            # that lint and the rate solver keep measuring speech, not speech plus music.
            from . import music
            bed = music.build(len(mix) / config.SAMPLE_RATE, self.chapters,
                              gain=config.MUSIC_GAIN, dark=self.dark_ranges)
            n = min(len(mix), len(bed))
            mix = mix.copy()
            mix[:n] = mix[:n] + bed[:n]
            peak = float(np.abs(mix).max())
            if peak > 0.99:                      # only ever attenuate, never pump
                mix *= 0.99 / peak
        tts.write_wav(path, mix)

    def write_chapters(self, path: Path) -> None:
        lines = []
        for t, name in self.chapters:
            m, s = divmod(int(t), 60)
            lines.append(f"{m:02d}:{s:02d} {name}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(script: Script, clips: list[tts.Clip], *, smoke: bool = False) -> Schedule:
    """Lay every beat out on a single timeline.

    In smoke mode each distinct visual gets a fixed short span and the audio is silence,
    so a full dry run of every scene costs about a minute instead of the full render.
    """
    pieces: list[np.ndarray] = [tts.silence(config.HEAD_SILENCE)]
    cursor = config.HEAD_SILENCE

    segments: list[Segment] = []
    cur_visual: Visual | None = None
    seg_start = 0.0
    sfx_marks: list[tuple[float, str]] = []
    chapters: list[tuple[float, str]] = []
    seen_sections: set[str] = set()

    spoken_before = False       # has any line been laid down yet
    last_ended_beat = False     # did a visual change or pause just end a beat

    clip_iter = iter(clips)

    def close_segment(at: float) -> None:
        nonlocal seg_start
        if segments or cur_visual is not None or at > 0:
            segments.append(Segment(seg_start, at, cur_visual))
        seg_start = at

    for beat in script.beats:
        if beat.visual is not cur_visual:
            close_segment(cursor)
            cur_visual = beat.visual
            last_ended_beat = True   # new visual = new paragraph, so a longer gap

        if beat.section and beat.section not in seen_sections:
            seen_sections.add(beat.section)
            chapters.append((cursor, beat.section))

        if beat.kind == "speak":
            clip = next(clip_iter)
            if smoke:
                cursor += 0.0            # spans are fixed below in smoke mode
            else:
                if spoken_before:
                    # Clips are trimmed to their speech, so the gap between lines is set
                    # here rather than inherited from the TTS backend's padding.
                    gap = config.SENTENCE_GAP if last_ended_beat else config.LINE_GAP
                    pieces.append(tts.silence(gap))
                    cursor += gap
                pieces.append(clip.samples)
                cursor += clip.duration
                spoken_before = True
            last_ended_beat = False
        elif beat.kind == "pause":
            if not smoke:
                pieces.append(tts.silence(beat.seconds))
                cursor += beat.seconds
            # An explicit pause already supplies the space; don't stack a gap on top.
            last_ended_beat = False
        elif beat.kind == "sfx":
            sfx_marks.append((cursor, beat.name))

    close_segment(cursor)
    segments = [s for s in segments if s.duration > 1e-3 or smoke]

    if smoke:
        # Rebuild spans as fixed-length so every visual is exercised quickly.
        t = 0.0
        for seg in segments:
            seg.start, seg.end = t, t + SMOKE_SEGMENT
            t += SMOKE_SEGMENT
        duration = t
        audio = tts.silence(duration)
        chapters = []
    else:
        pieces.append(tts.silence(config.TAIL_SILENCE))
        audio = np.concatenate(pieces) if pieces else tts.silence(0.1)
        duration = len(audio) / config.SAMPLE_RATE
        if segments:
            segments[-1].end = duration
        for at, name in sfx_marks:
            sfx.mix_into(audio, name, at)
        # Renderer-emitted cues (HOUSE_STYLE §12): a scene that opted in declares its own
        # sub-beat moments — a cross landing, a cable snapping — against its MEASURED span,
        # which is the only clock those moments exist on. Hand-placed [SFX:] lines can only
        # hit beat boundaries; these land exactly where the drawing does, and re-land
        # correctly whenever the audio re-paces. Imported lazily: schedule stays free of
        # cairo except when an episode actually uses cues.
        for seg in segments:
            if seg.visual is not None and seg.visual.get("cue") == "on":
                from . import scenes
                for off, name, g in scenes.cues(seg.visual, seg.duration):
                    sfx.mix_into(audio, name, seg.start + off,
                                 gain=config.SFX_GAIN * g)
        peak = float(np.max(np.abs(audio))) or 1.0
        if peak > 0.98:
            audio = audio * (0.98 / peak)

    dark: list[tuple[float, float]] = []
    if not smoke:
        for seg in segments:
            if seg.visual is not None and seg.visual.get("mood") == "dark":
                # Merge adjacent opted-in beats into one range, so the bed crossfades
                # once per sequence rather than once per visual.
                if dark and seg.start - dark[-1][1] < 0.75:
                    dark[-1] = (dark[-1][0], seg.end)
                else:
                    dark.append((seg.start, seg.end))

    return Schedule(segments=segments, audio=audio.astype(np.float32),
                    duration=duration, chapters=chapters, dark_ranges=dark)
