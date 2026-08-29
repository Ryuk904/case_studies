"""Channel identity — avatar, banner, watermark — drawn in code, not generated.

An image model is the wrong tool for these. A logo and a banner are almost entirely
typography, and diffusion models still mangle letterforms; worse, the avatar is displayed at
98px, where a downscaled raster of AI-drawn type turns to mud while vector-rendered type
stays crisp. Drawing them here also means the identity is the *same* palette and the *same*
font stack as every frame of every episode, by construction rather than by eye.

    python -m pipeline.brand            writes everything to assets/brand/

The mark is a pulse trace that spikes once and then flatlines. It reads at 98px, it means
the same thing to an engineer and to somebody who has never written code, and it is a single
stroke — which is what survives being shrunk into a circle in a sidebar.
"""

from __future__ import annotations

import math
from pathlib import Path

import cairo

from . import config, sketch

OUT = Path(__file__).resolve().parent.parent / "assets" / "brand"

# YouTube crops every avatar to a circle. Anything outside the inscribed circle is thrown
# away, so the mark is built against the circle, not the square.
AVATAR = 800

# Banner geometry is a hard spec, not a preference. The upload is 2560x1440, but the only
# region guaranteed to be visible on every device is the centre 1546x423 — phones crop to
# exactly that. Desktop shows 2560x423, TV shows the whole 2560x1440. So: nothing that
# carries meaning may leave the safe box, and everything outside it is atmosphere that some
# viewers will never see.
BANNER_W, BANNER_H = 2560, 1440
SAFE_W, SAFE_H = 1546, 423


def _surface(w: int, h: int, bg: tuple[float, float, float] | None = config.BG):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    if bg is not None:
        ctx.set_source_rgb(*bg)
        ctx.paint()
    return surf, ctx


def pulse(ctx: cairo.Context, cx: float, cy: float, w: float, h: float,
          width: float, *, spike: tuple[float, float, float] = config.ACCENT,
          flat: tuple[float, float, float] = config.FAIL) -> None:
    """A heartbeat that spikes once and then goes flat.

    Drawn as two strokes in two colours so the flatline is unmistakably the failure — one
    continuous amber line reads as a graph, and a graph is not what this is.
    """
    x0, x1 = cx - w / 2, cx + w / 2
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_width(width)

    # Live half: flat, a small dip, then one tall spike.
    ctx.set_source_rgb(*spike)
    pts = [(x0, cy), (x0 + w * 0.20, cy), (x0 + w * 0.26, cy + h * 0.22),
           (x0 + w * 0.33, cy - h * 0.50), (x0 + w * 0.40, cy + h * 0.16),
           (x0 + w * 0.46, cy)]
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()

    # Dead half: nothing, all the way out.
    ctx.set_source_rgb(*flat)
    ctx.move_to(x0 + w * 0.46, cy)
    ctx.line_to(x1, cy)
    ctx.stroke()
    ctx.restore()


def mark(ctx: cairo.Context, cx: float, cy: float, size: float) -> None:
    """The ring-and-pulse mark at any size, in its own fixed proportions.

    Factored out because the banner must not re-derive it. Stretching the bare trace across
    a 2400px banner flattened the spike into a zigzag that no longer read as a heartbeat —
    the mark only works at its own aspect, so the banner composites the whole mark instead
    of redrawing the line wider.
    """
    ctx.save()
    ctx.set_source_rgb(*config.INK)
    ctx.set_line_width(size * 0.0175)
    ctx.arc(cx, cy, size * 0.435, 0, math.tau)
    ctx.stroke()
    ctx.restore()
    pulse(ctx, cx, cy, size * 0.66, size * 0.46, size * 0.0575)


def avatar(size: int = AVATAR, *, ring: bool = True,
           word: bool = True) -> cairo.ImageSurface:
    """Channel avatar. `word=False` drops the wordmark for a symbol-only mark.

    Both are provided because they win at different sizes, and YouTube only lets you upload
    one. With the word it is stronger at 98px — the channel page and search results — and
    turns to mush at 48px in comment threads. Without it the trace can be drawn half again
    as large and stays sharp everywhere, at the cost of never spelling the name out.
    """
    surf, ctx = _surface(size, size)
    s = size / 800.0
    cx = cy = size / 2

    if word:
        if ring:
            ctx.set_source_rgb(*config.INK)
            ctx.set_line_width(14 * s)
            ctx.arc(cx, cy, size * 0.435, 0, math.tau)
            ctx.stroke()
        pulse(ctx, cx, cy - 34 * s, size * 0.60, size * 0.30, 30 * s)
        sketch.text(ctx, "POSTMORTEM", cx, cy + 150 * s, 74 * s, config.INK,
                    config.FONT_SANS, align="center", bold=True)
    else:
        mark(ctx, cx, cy, size)
    return surf


def watermark(size: int = 150) -> cairo.ImageSurface:
    """The branding overlay that sits in the corner of every video. Transparent, ink only."""
    surf, ctx = _surface(size, size, bg=None)
    pulse(ctx, size / 2, size / 2, size * 0.86, size * 0.44, size * 0.055,
          spike=config.INK, flat=config.INK)
    return surf


def banner() -> cairo.ImageSurface:
    surf, ctx = _surface(BANNER_W, BANNER_H)
    cx, cy = BANNER_W / 2, BANNER_H / 2

    # Atmosphere first, outside the safe box — TV and wide desktop get depth, phones lose
    # nothing that matters.
    g = cairo.RadialGradient(cx, cy, 120, cx, cy, BANNER_W * 0.62)
    g.add_color_stop_rgba(0.0, *config.BG_DEEP, 1.0)
    g.add_color_stop_rgba(1.0, *config.BG, 1.0)
    ctx.set_source(g)
    ctx.paint()

    # A single flat line all the way across, under the type.
    #
    # Its height matters more than it looks. Desktop shows 2560x423 — the *same* vertical
    # band as the phone crop, only wider — so the difference between phone and desktop is
    # purely horizontal, and anything placed above or below that 423px band is seen on
    # televisions and nowhere else. Sitting at cy+250 this rule was TV-only. Inside the band
    # it does the job it was drawn for: the flatline runs off both edges of a desktop
    # browser, and a phone simply sees a shorter piece of it.
    ctx.save()
    ctx.set_source_rgba(*config.FAIL, 0.30)
    ctx.set_line_width(6)
    ctx.move_to(0, cy + 175)
    ctx.line_to(BANNER_W, cy + 175)
    ctx.stroke()
    ctx.restore()

    # Mark left, type right, everything budgeted against the 423px safe box rather than the
    # 1440px canvas — the canvas is what most viewers never see.
    mark(ctx, cx - 620, cy, 250)

    x = cx - 460
    sketch.text(ctx, "POSTMORTEM", x, cy + 10, 130, config.INK,
                config.FONT_SANS, bold=True)
    sketch.text(ctx, config.TAGLINE, x, cy + 78, 42, config.MUTED,
                config.FONT_SANS)
    sketch.text(ctx, "new case study every other week", x, cy + 140, 36,
                config.ACCENT, config.FONT_SANS)
    return surf


def safe_area_proof() -> cairo.ImageSurface:
    """The banner with the device crops drawn on top. Not for upload — for checking."""
    surf = banner()
    ctx = cairo.Context(surf)
    cx, cy = BANNER_W / 2, BANNER_H / 2
    boxes = [(SAFE_W, SAFE_H, config.OK, "PHONE — always visible"),
             (1855, SAFE_H, config.ACCENT, "TABLET"),
             (BANNER_W, SAFE_H, config.FAIL, "DESKTOP")]
    ctx.set_line_width(5)
    ctx.set_dash([22, 16])
    for w, h, col, label in boxes:
        ctx.set_source_rgb(*col)
        ctx.rectangle(cx - w / 2, cy - h / 2, w, h)
        ctx.stroke()
        sketch.text(ctx, label, cx - w / 2 + 16, cy - h / 2 - 18, 34, col,
                    config.FONT_SANS, bold=True)
    return surf


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("avatar_800.png", avatar(800)),
        ("avatar_icon_800.png", avatar(800, word=False)),
        ("avatar_98_proof.png", avatar(98)),      # what a sidebar actually shows
        ("watermark_150.png", watermark(150)),
        ("banner_2560x1440.png", banner()),
        ("banner_safe_area_proof.png", safe_area_proof()),
    ]
    for name, surf in jobs:
        path = OUT / name
        surf.write_to_png(str(path))
        print(f"  wrote {path.relative_to(OUT.parent.parent)}  "
              f"({surf.get_width()}x{surf.get_height()})")


if __name__ == "__main__":
    print("brand assets ->", OUT)
    build()
