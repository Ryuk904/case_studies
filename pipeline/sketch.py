"""Hand-drawn cairo primitives.

Everything visible in an episode is drawn through this module. It knows about pens, jitter
and text; it knows nothing about servers, databases or episodes.

THE CRITICAL INVARIANT — jitter must be stable across frames.
    A naive implementation seeds randomness per draw call, so a box that is on screen for
    six seconds re-jitters 180 times and shimmers like a bad GIF. Here every offset is
    derived deterministically from a `key` built out of the shape's own identity
    (coordinates, index). Same shape at the same place produces byte-identical jitter on
    every frame, so it sits still. Animate a shape by changing its geometry, never by
    changing its seed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cairo

from . import config

Color = tuple[float, float, float]


def count_up(target: str, progress: float) -> str:
    """Interpolate a numeric string from zero for a ticking counter.

    Digits are animated but every other character is preserved, so "$460,000,000" keeps
    its dollar sign and separators the whole way up and the layout never reflows.
    A number that counts is the cheapest retention device on a full-frame metric.
    """
    if progress >= 1.0:
        return target
    digits = [c for c in target if c.isdigit()]
    if not digits:
        return target
    value = int("".join(digits))
    shown = int(value * max(0.0, progress) ** 0.65)
    padded = str(shown).rjust(len(digits), "0")
    out, i = [], 0
    for c in target:
        if c.isdigit():
            out.append(padded[i])
            i += 1
        else:
            out.append(c)
    return "".join(out)


# ------------------------------------------------------------------- jitter
def _noise(key: int, salt: int = 0) -> float:
    """Deterministic pseudo-random in [-1, 1] from an integer key.

    A hash, not an RNG: no hidden state, so call order never affects output and frames
    stay reproducible.
    """
    x = (key * 0x9E3779B1 + salt * 0x85EBCA6B + config.SEED * 0xC2B2AE35) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 0x2545F491) & 0xFFFFFFFF
    x ^= x >> 13
    return (x / 0xFFFFFFFF) * 2.0 - 1.0


def _key(*parts: float) -> int:
    """Stable integer identity for a shape from its geometry."""
    k = 0
    for p in parts:
        k = (k * 31 + int(round(p * 4))) & 0xFFFFFFFF
    return k


# ---------------------------------------------------------------------- pen
@dataclass
class Pen:
    color: Color = config.INK
    width: float = config.STROKE
    roughness: float = config.ROUGHNESS
    passes: int = config.SKETCH_PASSES
    alpha: float = 1.0

    def apply(self, ctx: cairo.Context, pass_i: int = 0) -> None:
        r, g, b = self.color
        # Second pass sits lighter, like a pen retracing a line.
        a = self.alpha * (1.0 if pass_i == 0 else 0.55)
        ctx.set_source_rgba(r, g, b, a)
        ctx.set_line_width(self.width * (1.0 if pass_i == 0 else 0.75))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)


INK_PEN = Pen()
FAIL_PEN = Pen(color=config.FAIL)
OK_PEN = Pen(color=config.OK)
MUTED_PEN = Pen(color=config.MUTED, width=config.STROKE * 0.7, alpha=0.8)


# -------------------------------------------------------------------- paths
def _jittered_points(x1: float, y1: float, x2: float, y2: float,
                     pen: Pen, salt: int) -> list[tuple[float, float]]:
    """Sample a line into points nudged off-axis, more in the middle than the ends."""
    length = math.hypot(x2 - x1, y2 - y1)
    steps = max(2, int(length / 42))
    k = _key(x1, y1, x2, y2)
    nx, ny = -(y2 - y1) / (length or 1), (x2 - x1) / (length or 1)

    pts = []
    for i in range(steps + 1):
        t = i / steps
        # Ends are pinned so shapes still meet cleanly at corners.
        taper = math.sin(t * math.pi)
        off = _noise(k + i * 7919, salt) * pen.roughness * taper
        pts.append((x1 + (x2 - x1) * t + nx * off,
                    y1 + (y2 - y1) * t + ny * off))
    return pts


def _stroke_points(ctx: cairo.Context, pts: list[tuple[float, float]]) -> None:
    """Smooth polyline through points using quadratic midpoint interpolation."""
    ctx.move_to(*pts[0])
    for i in range(1, len(pts) - 1):
        mx = (pts[i][0] + pts[i + 1][0]) / 2
        my = (pts[i][1] + pts[i + 1][1]) / 2
        ctx.curve_to(pts[i][0], pts[i][1], pts[i][0], pts[i][1], mx, my)
    ctx.line_to(*pts[-1])


# ------------------------------------------------------------------ draw-on
# The nib position of the most recent partially-drawn stroke. scenes.py reads this to
# park a pen there, which is the visual signature of whiteboard animation: the viewer
# follows a point that is making the marks rather than watching shapes fade in.
TIP: tuple[float, float] | None = None


def reset_tip() -> None:
    global TIP
    TIP = None


def _truncate(pts: list[tuple[float, float]], progress: float) -> list[tuple[float, float]]:
    """Cut a polyline at `progress` of its arc length, interpolating the final segment."""
    global TIP
    if progress >= 1.0:
        return pts
    if progress <= 0.0:
        return []

    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
           for i in range(len(pts) - 1)]
    total = sum(seg)
    if total <= 0:
        return pts

    want = total * progress
    out, acc = [pts[0]], 0.0
    for i, d in enumerate(seg):
        if acc + d >= want:
            f = (want - acc) / d if d else 0.0
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
            y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
            out.append((x, y))
            TIP = (x, y)
            break
        acc += d
        out.append(pts[i + 1])
    return out


def line(ctx: cairo.Context, x1: float, y1: float, x2: float, y2: float,
         pen: Pen = INK_PEN, progress: float = 1.0) -> None:
    if progress <= 0.0:
        return
    for p in range(pen.passes):
        pen.apply(ctx, p)
        pts = _truncate(_jittered_points(x1, y1, x2, y2, pen, salt=p * 101), progress)
        if len(pts) < 2:
            continue
        _stroke_points(ctx, pts)
        ctx.stroke()


def rect(ctx: cairo.Context, x: float, y: float, w: float, h: float,
         pen: Pen = INK_PEN, fill: Color | None = None, fill_alpha: float = 1.0,
         overshoot: float = 4.0, progress: float = 1.0) -> None:
    """Rough rectangle. Corners overshoot slightly, the way a real pen runs past.

    Under draw-on the four sides are drawn in sequence, so the box is traced rather than
    appearing all at once.
    """
    if progress <= 0.0:
        return
    if fill is not None:
        ctx.set_source_rgba(*fill, fill_alpha * min(1.0, progress * 1.6))
        ctx.move_to(x, y)
        ctx.line_to(x + w, y)
        ctx.line_to(x + w, y + h)
        ctx.line_to(x, y + h)
        ctx.close_path()
        ctx.fill()

    k = _key(x, y, w, h)
    o = lambda i: overshoot * abs(_noise(k, i))  # noqa: E731
    sides = [
        (x - o(1), y, x + w + o(2), y),
        (x + w, y - o(3), x + w, y + h + o(4)),
        (x + w + o(5), y + h, x - o(6), y + h),
        (x, y + h + o(7), x, y - o(8)),
    ]
    # Weight each side by its length so the nib moves at a constant speed round the box.
    lens = [math.hypot(s[2] - s[0], s[3] - s[1]) for s in sides]
    total = sum(lens) or 1.0
    want, acc = total * progress, 0.0
    for s, ln in zip(sides, lens):
        if acc >= want:
            break
        line(ctx, *s, pen, progress=min(1.0, (want - acc) / ln if ln else 1.0))
        acc += ln


def ellipse(ctx: cairo.Context, cx: float, cy: float, rx: float, ry: float,
            pen: Pen = INK_PEN, fill: Color | None = None, fill_alpha: float = 1.0,
            progress: float = 1.0) -> None:
    """Rough ellipse. Under draw-on the outline is swept round like a drawn circle."""
    global TIP
    if progress <= 0.0:
        return
    k = _key(cx, cy, rx, ry)
    steps = 42

    if fill is not None:
        ctx.set_source_rgba(*fill, fill_alpha * min(1.0, progress * 1.6))
        for i in range(steps + 1):
            a = i / steps * math.tau
            (ctx.move_to if i == 0 else ctx.line_to)(cx + math.cos(a) * rx, cy + math.sin(a) * ry)
        ctx.close_path()
        ctx.fill()

    # Overdraw slightly past the start, like closing a hand-drawn circle.
    total = steps + 3
    drawn = total if progress >= 1.0 else max(2, int(total * progress))
    for p in range(pen.passes):
        pen.apply(ctx, p)
        for i in range(drawn):
            a = i / steps * math.tau
            j = _noise(k + i * 7919, p * 313) * pen.roughness
            x, y = cx + math.cos(a) * (rx + j), cy + math.sin(a) * (ry + j)
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
            if p == 0 and i == drawn - 1 and progress < 1.0:
                TIP = (x, y)
        ctx.stroke()


def arrow(ctx: cairo.Context, x1: float, y1: float, x2: float, y2: float,
          pen: Pen = INK_PEN, head: float = 16.0, progress: float = 1.0) -> None:
    if progress <= 0.0:
        return
    # Shaft first, head only once the shaft has actually arrived.
    shaft = min(1.0, progress / 0.82)
    line(ctx, x1, y1, x2, y2, pen, progress=shaft)
    if progress < 0.82:
        return
    tip = min(1.0, (progress - 0.82) / 0.18)
    ang = math.atan2(y2 - y1, x2 - x1)
    for side in (+1, -1):
        a = ang + math.pi + side * 0.42
        line(ctx, x2, y2, x2 + math.cos(a) * head, y2 + math.sin(a) * head, pen,
             progress=tip)


def flow(ctx: cairo.Context, x1: float, y1: float, x2: float, y2: float,
         phase: float, color: Color = config.FAIL, n: int = 3,
         radius: float = 7.0) -> None:
    """Dots travelling along an edge — shows that something is actually moving.

    A static arrow says "A connects to B". Moving dots say "orders are pouring through
    right now", which is the difference between a diagram and a story beat.
    """
    ctx.set_source_rgb(*color)
    for i in range(n):
        t = (phase + i / n) % 1.0
        # Fade in and out at the ends so dots do not pop at the boxes.
        a = min(1.0, min(t, 1.0 - t) * 6.0)
        ctx.set_source_rgba(*color, a)
        ctx.arc(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, radius, 0, math.tau)
        ctx.fill()


def pen_nib(ctx: cairo.Context, x: float, y: float, scale: float = 1.0) -> None:
    """A simple pen resting at the point currently being drawn."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)
    ctx.rotate(-0.62)
    ctx.set_source_rgba(0.10, 0.11, 0.13, 0.92)
    ctx.move_to(0, 0)                 # nib
    ctx.line_to(-7, -17)
    ctx.line_to(7, -17)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(0.22, 0.24, 0.28, 0.92)
    ctx.rectangle(-7, -17, 14, 64)    # barrel
    ctx.fill()
    ctx.set_source_rgba(*config.HILITE, 0.95)
    ctx.rectangle(-7, -17, 14, 9)     # band
    ctx.fill()
    ctx.restore()


def wash(ctx: cairo.Context, x: float, y: float, w: float, h: float,
         color: Color = config.HILITE, alpha: float = 0.55) -> None:
    """Highlighter stroke behind text. Uneven top and bottom edges, like a real marker."""
    k = _key(x, y, w, h)
    ctx.set_source_rgba(*color, alpha)
    ctx.move_to(x, y + _noise(k, 1) * 3)
    ctx.line_to(x + w, y + _noise(k, 2) * 3)
    ctx.line_to(x + w, y + h + _noise(k, 3) * 3)
    ctx.line_to(x, y + h + _noise(k, 4) * 3)
    ctx.close_path()
    ctx.fill()


# --------------------------------------------------------------------- text
_FONT_CACHE: dict[tuple[str, ...], str] = {}


def resolve_font(chain: list[str]) -> str:
    """First font in the chain that cairo actually resolves to something distinct.

    Cairo's toy API silently substitutes a default for a missing family, so we compare
    rendered advance widths: if a candidate measures identically to a deliberately
    nonsense family, it was substituted and we move on.
    """
    key = tuple(chain)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 8, 8)
    ctx = cairo.Context(surf)
    ctx.set_font_size(48)

    def width(family: str) -> float:
        ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        return ctx.text_extents("HAMBURGEFONTSTIV misc 0123")[4]

    fallback = width("__definitely_not_a_font__")
    chosen = chain[-1]
    for family in chain:
        if abs(width(family) - fallback) > 0.5:
            chosen = family
            break

    _FONT_CACHE[key] = chosen
    return chosen


def text(ctx: cairo.Context, s: str, x: float, y: float, size: float,
         color: Color = config.INK, chain: list[str] | None = None,
         align: str = "left", bold: bool = False, alpha: float = 1.0,
         progress: float = 1.0) -> tuple[float, float]:
    """Draw a single line of text. Returns (width, height). y is the BASELINE.

    Under draw-on, `progress` wipes the text in left to right behind a clip rectangle,
    which reads as handwriting appearing rather than a caption fading up.
    """
    family = resolve_font(chain or config.FONT_SANS)
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)

    ext = ctx.text_extents(s)
    w, h = ext[4], ext[3]
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w

    if progress <= 0.0:
        return w, h

    ctx.save()
    if progress < 1.0:
        ctx.rectangle(x - 4, y - h - size * 0.35, w * progress + 4, h + size * 0.75)
        ctx.clip()
        global TIP
        TIP = (x + w * progress, y - h * 0.35)
    ctx.set_source_rgba(*color, alpha)
    ctx.move_to(x, y)
    ctx.show_text(s)
    ctx.restore()
    return w, h


def text_size(ctx: cairo.Context, s: str, size: float,
              chain: list[str] | None = None, bold: bool = False) -> tuple[float, float]:
    """Measure without drawing — used by layout code before it commits to positions."""
    family = resolve_font(chain or config.FONT_SANS)
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    return ext[4], ext[3]


def fit_size(ctx: cairo.Context, s: str, size: float, max_w: float,
             chain: list[str] | None = None, bold: bool = False,
             min_size: float = 12.0) -> float:
    """Largest font size <= `size` at which `s` fits inside `max_w`.

    Nothing in an episode should ever specify a point size and hope. Big metrics are the
    worst offender: "$460,000,000" is three times the width of "$460M" at the same size,
    so a fixed SZ_METRIC either overflows the frame or is set tiny for the safe case.
    """
    if not s:
        return size
    w = text_size(ctx, s, size, chain, bold)[0]
    if w <= max_w:
        return size
    return max(min_size, size * max_w / w)


def wrap(ctx: cairo.Context, s: str, size: float, max_w: float,
         chain: list[str] | None = None, bold: bool = False) -> list[str]:
    words, lines, cur = s.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if text_size(ctx, trial, size, chain, bold)[0] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrap_balanced(ctx: cairo.Context, s: str, size: float, max_w: float,
                  chain: list[str] | None = None, bold: bool = False) -> list[str]:
    """Wrap without leaving an orphan word on the last line.

    Greedy wrapping put "it" alone on line two of "delete dead code the day you retire it",
    which looks like a mistake on a title card. Narrow the measure as far as possible
    without adding a line, and the text evens itself out.
    """
    best = wrap(ctx, s, size, max_w, chain, bold)
    if len(best) < 2:
        return best
    target = len(best)
    for frac in (0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60):
        cand = wrap(ctx, s, size, max_w * frac, chain, bold)
        if len(cand) != target:
            break
        best = cand
    return best


# -------------------------------------------------------------------- canvas
def fit_block(ctx: cairo.Context, s: str, size: float, max_w: float,
              max_h: float = 1e9, chain: list[str] | None = None,
              bold: bool = False, line_ratio: float = 1.16,
              min_size: float = 18.0) -> tuple[float, list[str]]:
    """Largest size at which `s`, WRAPPED, fits inside (max_w, max_h). Returns the lines too.

    fit_size() sizes a single unwrapped string, so calling it on a sentence forces the whole
    sentence onto one line and shrinks it to a caption. Anything that wraps has to be fitted
    as a block: wrap, measure the widest line, shrink, repeat.
    """
    chain = chain or config.FONT_SANS
    while size > min_size:
        lines = wrap_balanced(ctx, s, size, max_w, chain, bold)
        widest = max((text_size(ctx, ln, size, chain, bold)[0] for ln in lines), default=0)
        if widest <= max_w and size * line_ratio * len(lines) <= max_h:
            return size, lines
        size *= 0.94
    return min_size, wrap_balanced(ctx, s, min_size, max_w, chain, bold)


# ------------------------------------------------------- dark-direction primitives
def glow(ctx: cairo.Context, cx: float, cy: float, radius: float,
         color: Color = config.FAIL, alpha: float = 0.30) -> None:
    """A soft radial bloom. On a near-black ground this is what gives the failure accent
    physical presence — a red outline reads as a colour, a red glow reads as heat."""
    g = cairo.RadialGradient(cx, cy, radius * 0.04, cx, cy, radius)
    g.add_color_stop_rgba(0, *color, alpha)
    g.add_color_stop_rgba(1, *color, 0.0)
    ctx.save()
    ctx.set_source(g)
    ctx.rectangle(cx - radius, cy - radius, radius * 2, radius * 2)
    ctx.fill()
    ctx.restore()


# Full-bleed paint must ignore the content pan.
#
# scenes._drift() translates the whole frame by a few whole pixels over a scene. Anything
# that fills "the frame" by drawing a 0,0,W,H rectangle is drawn INSIDE that translation, so
# it lands a few pixels short of two edges and leaves a strip of bare background behind. On a
# hero card that is a black seam down the red, and it is the kind of thing you only see once
# it is on a television. Measured on a hero metric card with a 10px pan: 71% of the rightmost
# 14px column was bare background.
#
# These two paint in DEVICE space instead, so the colour field and the vignette are the paper
# and the content moves over them.
def vignette(ctx: cairo.Context, cx: float, cy: float,
             inner: float = 0.0, outer: float = 0.72) -> None:
    """Darken toward the edges, lit around (cx, cy). Gives a flat frame depth and tells
    the eye where to land before it has read anything."""
    g = cairo.RadialGradient(cx, cy, config.W * 0.10, cx, cy, config.W * 0.80)
    g.add_color_stop_rgba(0, 0, 0, 0, inner)
    g.add_color_stop_rgba(1, 0, 0, 0, outer)
    ctx.save()
    ctx.set_source(g)                       # gradient built in USER space, before the reset
    m = ctx.get_matrix()
    ctx.identity_matrix()
    ctx.rectangle(0, 0, config.W, config.H)
    ctx.set_matrix(m)
    ctx.fill()
    ctx.restore()


def field(ctx: cairo.Context, color: Color, *, progress: float = 1.0,
          direction: str = "up") -> None:
    """A full-bleed colour panel, optionally sliding in. Section fields are how the episode
    shows a chapter change instead of announcing it."""
    p = max(0.0, min(1.0, progress))
    if p <= 0.0:
        return
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgb(*color)
    if direction == "up":
        h = config.H * p
        ctx.rectangle(0, config.H - h, config.W, h)
    elif direction == "down":
        ctx.rectangle(0, 0, config.W, config.H * p)
    elif direction == "left":
        w = config.W * p
        ctx.rectangle(config.W - w, 0, w, config.H)
    else:
        ctx.rectangle(0, 0, config.W * p, config.H)
    ctx.fill()
    ctx.restore()


def smallcaps(ctx: cairo.Context, s: str, x: float, y: float, size: float,
              color: Color = config.MUTED, *, align: str = "left",
              track: float = 7.0, progress: float = 1.0) -> float:
    """Letter-spaced caps. Tracking is most of what separates an editorial label from a
    caption, and it costs nothing. Returns the total width."""
    s = s.upper()
    widths = [text_size(ctx, ch, size, config.FONT_SANS, bold=True)[0] for ch in s]
    total = sum(widths) + track * max(0, len(s) - 1)
    if align == "center":
        x -= total / 2
    elif align == "right":
        x -= total
    shown = int(len(s) * max(0.0, min(1.0, progress)) + 0.001)
    for ch, w in zip(s[:shown], widths[:shown]):
        text(ctx, ch, x, y, size, color, config.FONT_SANS, bold=True)
        x += w + track
    return total


_BACKDROP: cairo.ImageSurface | None = None


def _backdrop() -> cairo.ImageSurface:
    """The paper every frame starts from — built once, painted every frame.

    A flat #0E1013 fill was the EP04 note "the background needs to be better": subjects
    floated in a featureless void. This is still near-black, but it breathes — a vertical
    grade (cool lift at the top, falling darker at the foot) and a static seeded grain.
    The grain is STATIC by design: per-frame noise would defeat tools/shimmer.py and
    spend h264 bitrate on dust (HOUSE_STYLE §11 decided this before it was built).
    """
    global _BACKDROP
    if _BACKDROP is not None:
        return _BACKDROP
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, config.W, config.H)
    ctx = cairo.Context(surf)
    # Measured, not eyeballed: the first attempt spanned 11 levels of 255 top to bottom and
    # the note back was still "the background is all black". This spans ~45 and is visible
    # on a phone. A cool lift at the top, a warm bloom low-left where the light is, and the
    # foot falling away so subjects have something to stand against.
    g = cairo.LinearGradient(0, 0, 0, config.H)
    g.add_color_stop_rgb(0.00, 0.135, 0.160, 0.208)
    g.add_color_stop_rgb(0.48, *config.BG)
    g.add_color_stop_rgb(1.00, 0.043, 0.051, 0.067)
    ctx.set_source(g)
    ctx.paint()
    bloom = cairo.RadialGradient(config.W * 0.30, config.H * 0.62, 40,
                                 config.W * 0.30, config.H * 0.62, config.W * 0.72)
    bloom.add_color_stop_rgba(0, 0.36, 0.30, 0.22, 0.10)
    bloom.add_color_stop_rgba(1, 0.36, 0.30, 0.22, 0.0)
    ctx.set_source(bloom)
    ctx.paint()
    import numpy as np
    rng = np.random.default_rng(config.SEED * 7919)
    xs = rng.uniform(0, config.W, 2600)
    ys = rng.uniform(0, config.H, 2600)
    aa = rng.uniform(0.012, 0.05, 2600)
    ss = rng.uniform(0.6, 1.5, 2600)
    for x, y, a, s in zip(xs, ys, aa, ss):
        ctx.set_source_rgba(1.0, 0.97, 0.92, float(a))
        ctx.rectangle(float(x), float(y), float(s), float(s))
        ctx.fill()
    surf.flush()
    _BACKDROP = surf
    return surf


def photo_backdrop(ctx: cairo.Context, name: str, *, darken: float = 0.55,
                   blur: int = 14, tint: Color | None = None,
                   alpha: float = 1.0, desat: float = 0.72) -> bool:
    """Paint a treated free-licence photograph full-bleed, in DEVICE space.

    Device space for the same reason sketch.field() uses it: this is the paper, and the
    content pans over it. Returns False when the plate was never fetched, so a scene
    degrades to the graded backdrop instead of failing a render.
    """
    from . import photo
    surf = photo.plate(name, darken=darken, blur=blur, tint=tint, desat=desat)
    if surf is None:
        return False
    ctx.save()
    m = ctx.get_matrix()
    ctx.identity_matrix()
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(alpha)
    ctx.set_matrix(m)
    ctx.restore()
    return True


def new_surface() -> tuple[cairo.ImageSurface, cairo.Context]:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, config.W, config.H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_source_surface(_backdrop(), 0, 0)
    ctx.paint()
    return surf, ctx


def surface_to_rgb(surf: cairo.ImageSurface) -> "np.ndarray":  # noqa: F821
    """cairo BGRA -> RGB for the encoder.

    The background is always opaque, so there is no un-premultiply step to get wrong.
    """
    import numpy as np
    surf.flush()
    buf = np.frombuffer(surf.get_data(), dtype=np.uint8)
    arr = buf.reshape(config.H, surf.get_stride() // 4, 4)[:, :config.W, :]
    return arr[:, :, [2, 1, 0]].copy()
