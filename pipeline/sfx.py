"""Synthesised sound effects.

Every effect is generated from numpy. Nothing is loaded from disk and nothing is licensed,
which means an episode can never be demonetised or struck over a sample, and the repo stays
free of binary assets.

Keep these subtle. They punctuate a beat; they are not the content. config.SFX_GAIN holds
them well under the voice.
"""

from __future__ import annotations

import numpy as np

from . import config

SR = config.SAMPLE_RATE


def _t(dur: float) -> np.ndarray:
    return np.linspace(0.0, dur, int(SR * dur), endpoint=False, dtype=np.float32)


def _decay(n: int, k: float = 8.0) -> np.ndarray:
    return np.exp(-k * np.linspace(0.0, 1.0, n, dtype=np.float32))


def pop(dur: float = 0.09) -> np.ndarray:
    """Soft click for a node appearing."""
    t = _t(dur)
    tone = np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t)
    return (tone * _decay(len(t), 26.0) * 0.5).astype(np.float32)


def tick(dur: float = 0.05) -> np.ndarray:
    t = _t(dur)
    return (np.sin(2 * np.pi * 2200 * t) * _decay(len(t), 45.0) * 0.35).astype(np.float32)


def thud(dur: float = 0.45) -> np.ndarray:
    """Low hit for a failure reveal. Pitch drops as it decays."""
    t = _t(dur)
    freq = 120.0 * np.exp(-3.0 * t)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return (np.sin(phase) * _decay(len(t), 7.0)).astype(np.float32)


def whoosh(dur: float = 0.55) -> np.ndarray:
    """Band-swept noise for a scene transition."""
    n = int(SR * dur)
    noise = np.random.default_rng(config.SEED).standard_normal(n).astype(np.float32)
    # One-pole lowpass whose cutoff sweeps up then down, done as a cheap moving average.
    env = np.sin(np.linspace(0, np.pi, n, dtype=np.float32))
    win = np.maximum(2, (60 * (1.0 - env)).astype(int))
    out = np.empty(n, dtype=np.float32)
    acc, k = 0.0, 0
    for i in range(n):
        k = win[i]
        acc += (noise[i] - acc) / k
        out[i] = acc
    return (out * env * 2.4).astype(np.float32)


def ping(dur: float = 0.85) -> np.ndarray:
    """Alert chime for an alarm or a pager — brighter and longer than `tick`, so it reads
    as something demanding attention rather than something being checked off. Added per
    HOUSE_STYLE §11 ("Add a ping for alarms")."""
    t = _t(dur)
    tone = (np.sin(2 * np.pi * 1175 * t)
            + 0.55 * np.sin(2 * np.pi * 1760 * t)
            + 0.20 * np.sin(2 * np.pi * 2350 * t))
    out = tone * _decay(len(t), 9.0) * 0.4
    # A quiet echo a fifth of a second later, so it hangs in the air like a real alert.
    off = int(SR * 0.2)
    out[off:] += out[:len(out) - off] * 0.35
    return out.astype(np.float32)


def riser(dur: float = 1.2) -> np.ndarray:
    """Tension build before a number reveal. Use at most once per episode."""
    t = _t(dur)
    freq = 200.0 * np.exp(1.6 * t / max(dur, 1e-6))
    phase = 2 * np.pi * np.cumsum(freq) / SR
    env = (t / max(dur, 1e-6)) ** 2
    return (np.sin(phase) * env * 0.5).astype(np.float32)


EFFECTS = {
    "pop": pop,
    "tick": tick,
    "thud": thud,
    "whoosh": whoosh,
    "riser": riser,
    "ping": ping,
}


def get(name: str) -> np.ndarray:
    if name not in EFFECTS:
        raise KeyError(f"unknown SFX {name!r}; known: {', '.join(sorted(EFFECTS))}")
    return EFFECTS[name]()


def mix_into(track: np.ndarray, name: str, at_seconds: float,
             gain: float = config.SFX_GAIN) -> None:
    """Add an effect into `track` in place, clipped to the track's length."""
    fx = get(name) * gain
    start = int(at_seconds * SR)
    if start >= len(track):
        return
    end = min(len(track), start + len(fx))
    track[start:end] += fx[:end - start]
