"""A procedural ambient bed, synthesised per episode.

Written rather than licensed for the obvious reason — no attribution, no takedown, no
subscription — and for a less obvious one: because it is generated against the episode's own
timeline, it can change at section boundaries instead of looping indifferently underneath.

Deliberately almost nothing: a low drone, a fifth above it, a slow filtered noise swell, and
one soft bell at each chapter change. Anything with a melody competes with the narration, and
the narration is the product. Sits about 26 dB under the voice.

    bed = build(duration, marks=[(0.0, "hook"), (27.3, "context"), ...])
"""

from __future__ import annotations

import math

import numpy as np

from . import config

# Root note per section, in Hz. The takeaway lifts a whole tone; the breakdown sits lowest.
# Small moves — the point is that a viewer feels the chapter turn without noticing why.
ROOTS = {"hook": 55.00, "context": 58.27, "breakdown": 49.00, "takeaway": 65.41}
GAIN = 0.05                      # peak of the bed before the voice is mixed over it


def _drone(n: int, sr: int, f: float) -> np.ndarray:
    """A root plus its fifth and octave, slightly detuned so it breathes."""
    t = np.arange(n, dtype=np.float32) / sr
    out = np.zeros(n, dtype=np.float32)
    for mult, amp, detune in ((1.0, 1.00, 0.0), (1.5, 0.42, 0.13), (2.0, 0.22, -0.09)):
        out += amp * np.sin(2 * math.pi * (f * mult + detune) * t).astype(np.float32)
    # Slow amplitude drift, so a five-minute stretch never sits perfectly still.
    lfo = 0.82 + 0.18 * np.sin(2 * math.pi * 0.035 * t).astype(np.float32)
    return out * lfo / 1.64


def _air(n: int, sr: int, seed: int) -> np.ndarray:
    """Very dark filtered noise. Fills the space between the drone's harmonics."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n).astype(np.float32)
    # Two one-pole lowpasses in series, ~80 Hz. Cheap, and cheaper than an FFT here.
    a = math.exp(-2 * math.pi * 80.0 / sr)
    for _ in range(2):
        b = np.empty_like(x)
        acc = 0.0
        for i in range(0, n, 4096):                 # chunked to keep the loop out of Python
            blk = x[i:i + 4096]
            y = np.empty_like(blk)
            for k, s in enumerate(blk):
                acc = a * acc + (1 - a) * s
                y[k] = acc
            b[i:i + 4096] = y
        x = b
    peak = float(np.abs(x).max()) or 1.0
    t = np.arange(n, dtype=np.float32) / sr
    swell = 0.5 + 0.5 * np.sin(2 * math.pi * 0.017 * t - 1.2).astype(np.float32)
    return (x / peak) * swell * 0.5


def _bell(sr: int, f: float, seconds: float = 3.2) -> np.ndarray:
    """A soft struck tone for a chapter change. Exponential decay, no attack transient."""
    n = int(sr * seconds)
    t = np.arange(n, dtype=np.float32) / sr
    env = np.exp(-t * 1.5).astype(np.float32)
    tone = (np.sin(2 * math.pi * f * t)
            + 0.5 * np.sin(2 * math.pi * f * 2.01 * t)
            + 0.25 * np.sin(2 * math.pi * f * 3.02 * t)).astype(np.float32)
    attack = np.minimum(1.0, t / 0.012).astype(np.float32)
    return tone * env * attack / 1.75


def _tension(n: int, sr: int, f: float) -> np.ndarray:
    """The darker, sparser variant (HOUSE_STYLE §12) a beat range can opt into.

    Where the standard drone stacks root + fifth + octave, this is a bare sub-root with a
    minor third breathing above it, under a slow throb — fewer notes, lower, tenser. It
    replaces most of the normal bed inside its range rather than being added on top, so
    the overall level never rises: texture sits UNDER the voice and must never announce
    itself.
    """
    t = np.arange(n, dtype=np.float32) / sr
    sub = np.sin(2 * math.pi * (f * 0.5) * t).astype(np.float32)
    third = 0.34 * np.sin(2 * math.pi * (f * 0.5 * 1.1892 + 0.07) * t).astype(np.float32)
    throb = 0.70 + 0.30 * np.sin(2 * math.pi * 0.09 * t - math.pi / 2).astype(np.float32)
    return (sub + third) / 1.34 * throb


def build(duration: float, marks: list[tuple[float, str]] | None = None,
          sr: int | None = None, gain: float = GAIN,
          dark: list[tuple[float, float]] | None = None) -> np.ndarray:
    """A bed `duration` seconds long. `marks` are (seconds, section) chapter boundaries.

    `dark` is a list of (start, end) second ranges that opt into the tension variant —
    authored per beat via mood="dark" and collected by schedule.py. Empty or None leaves
    the output bit-identical to the pre-§12 bed.
    """
    sr = sr or config.SAMPLE_RATE
    n = int(duration * sr)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    marks = sorted(marks or [(0.0, "breakdown")])
    if marks[0][0] > 0:
        marks.insert(0, (0.0, marks[0][1]))

    out = _air(n, sr, seed=config.SEED)
    for i, (start, section) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else duration
        a, b = int(start * sr), min(n, int(end * sr))
        if b <= a:
            continue
        seg = _drone(b - a, sr, ROOTS.get(section, ROOTS["breakdown"]))
        # Cross-fade between sections rather than cutting; a drone that switches is a click.
        fade = min(int(sr * 2.5), (b - a) // 2)
        if fade > 0:
            ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
            seg[:fade] *= ramp
            seg[-fade:] *= ramp[::-1]
        out[a:b] += seg
        if i > 0:
            bell = _bell(sr, ROOTS.get(section, ROOTS["breakdown"]) * 4)
            e = min(n, a + len(bell))
            out[a:e] += bell[:e - a] * 0.5

    # Tension ranges: crossfade the normal bed down and the sparse dark layer in. Done
    # with an envelope rather than a splice so a range boundary can never click.
    for start, end in dark or []:
        a, b = max(0, int(start * sr)), min(n, int(end * sr))
        if b - a < sr // 4:
            continue
        env = np.ones(b - a, dtype=np.float32)
        fade = min(int(sr * 2.0), (b - a) // 2)
        if fade > 0:
            ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
            env[:fade] = ramp
            env[-fade:] = ramp[::-1]
        # Root from whichever section this range starts in, an octave down via _tension.
        section = "breakdown"
        for ms, name in marks:
            if ms <= start:
                section = name
        layer = _tension(b - a, sr, ROOTS.get(section, ROOTS["breakdown"]))
        out[a:b] = out[a:b] * (1.0 - 0.62 * env) + layer * env * 0.9

    peak = float(np.abs(out).max()) or 1.0
    out = (out / peak) * gain
    # Ease the very start and end, so the bed arrives and leaves rather than switching on.
    ramp = int(sr * 2.0)
    if n > ramp * 2:
        out[:ramp] *= np.linspace(0.0, 1.0, ramp, dtype=np.float32)
        out[-ramp:] *= np.linspace(1.0, 0.0, ramp, dtype=np.float32)
    return out.astype(np.float32)
